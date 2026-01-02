import os
import time
import requests
import shutil
from bs4 import BeautifulSoup

BASE_URL = "https://www.westonaprice.org"
MAIN_PAGE = "https://www.westonaprice.org/health-topics/"
BASE_FOLDER = "articles_for_site1"
ZIP_NAME = "articles_for_site1"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

os.makedirs(BASE_FOLDER, exist_ok=True)


# =========================
# SAFE REQUEST HELPER
# =========================
def fetch_url(url, headers, retries=3, timeout=30):
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.ReadTimeout:
            print(f"⏳ Timeout (attempt {attempt}/{retries}) → {url}")
        except requests.exceptions.ConnectionError as e:
            print(f"🌐 Connection error (attempt {attempt}/{retries}) → {e}")
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP error → {e}")
            break
        time.sleep(3)

    print(f"❌ Skipping after {retries} failed attempts → {url}")
    return None


def slug_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


# =========================
# HTML → MARKDOWN
# =========================
def html_to_markdown(content_div: BeautifulSoup) -> str:
    md = []

    allowed_tags = [
        "h1", "h2", "h3", "h4", "h5",
        "p", "br", "hr",
        "strong", "em", "b", "i",
        "ul", "ol", "li",
        "blockquote",
        "dl", "dt", "dd",
        "table", "thead", "tbody", "tfoot", "tr", "th", "td",
        "figure", "figcaption", "img",
        "pre", "code",
        "a"
    ]

    for el in content_div.find_all(allowed_tags, recursive=True):

        # ---------- HEADINGS ----------
        if el.name in ["h1", "h2", "h3", "h4", "h5"]:
            text = el.get_text(strip=True)
            if text:
                level = {
                    "h1": "#",
                    "h2": "##",
                    "h3": "###",
                    "h4": "####",
                    "h5": "#####"
                }[el.name]
                md.append(f"{level} {text}\n")

        # ---------- PARAGRAPH ----------
        elif el.name == "p":
            text = el.get_text(" ", strip=True)
            if text and text != "\xa0":
                md.append(f"{text}\n")

        # ---------- LINE BREAK ----------
        elif el.name == "br":
            md.append("")

        # ---------- HR ----------
        elif el.name == "hr":
            md.append("\n---\n")

        # ---------- LISTS ----------
        elif el.name in ["ul", "ol"]:
            for li in el.find_all("li", recursive=False):
                li_text = li.get_text(" ", strip=True)
                if li_text:
                    md.append(f"- {li_text}")
            md.append("")

        # ---------- BLOCKQUOTE ----------
        elif el.name == "blockquote":
            text = el.get_text(" ", strip=True)
            if text:
                md.append(f"> {text}\n")

        # ---------- DEFINITIONS ----------
        elif el.name == "dt":
            text = el.get_text(strip=True)
            if text:
                md.append(f"**{text}**")
        elif el.name == "dd":
            text = el.get_text(" ", strip=True)
            if text:
                md.append(f": {text}\n")

        # ---------- TABLE ----------
        elif el.name == "table":
            md.append("")
            for row in el.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    left = cells[0].get_text(" ", strip=True)
                    right = cells[1].get_text(" ", strip=True)
                    if left and right:
                        md.append(f"- **{left}** {right}")
            md.append("")

        # ---------- FIGURE ----------
        elif el.name == "figure":
            img = el.find("img")
            caption = el.find("figcaption")

            if img and img.get("src"):
                alt = img.get("alt", "").strip()
                md.append(f"![{alt}]({img['src']})")

            if caption:
                cap_text = caption.get_text(" ", strip=True)
                if cap_text:
                    md.append(f"*{cap_text}*\n")

        # ---------- IMAGE ----------
        elif el.name == "img" and el.parent.name != "figure":
            src = el.get("src")
            alt = el.get("alt", "")
            if src:
                md.append(f"![{alt}]({src})\n")

        # ---------- CODE ----------
        elif el.name == "pre":
            code = el.get_text()
            if code.strip():
                md.append(f"```\n{code}\n```\n")

        elif el.name == "code":
            text = el.get_text(strip=True)
            if text:
                md.append(f"`{text}`")

        # ---------- LINKS ----------
        elif el.name == "a":
            href = el.get("href")
            text = el.get_text(strip=True)
            if href and text:
                md.append(f"[{text}]({href})")

    return "\n".join(md).strip()


# =========================
# ARTICLE SCRAPER
# =========================
def scrape_article(article_url: str, category_folder: str):
    response = fetch_url(article_url, headers)
    if response is None:
        return

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1")
    content_div = soup.select_one("div.entry-content")

    if not title_tag or not content_div:
        print(f"⚠️ Missing content → {article_url}")
        return

    title = title_tag.get_text(strip=True)
    slug = slug_from_url(article_url)
    file_path = os.path.join(category_folder, f"{slug}.md")

    markdown_body = html_to_markdown(content_div)

    if len(markdown_body) < 300:
        print(f"⚠️ Low content → {article_url}")
        return

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"Source: {article_url}\n\n")
        f.write(markdown_body)

    print(f"   ✔ Saved: {slug}.md")


# =========================
# CATEGORY SCRAPER
# =========================
def scrape_category(name: str, url: str):
    category_slug = slug_from_url(url)
    category_folder = os.path.join(BASE_FOLDER, category_slug)
    os.makedirs(category_folder, exist_ok=True)

    print(f"\n📂 Category: {name}")
    print(f"Folder: {category_folder}")

    response = fetch_url(url, headers)
    if response is None:
        return

    soup = BeautifulSoup(response.text, "html.parser")

    article_links = soup.select("main.content h5 a")
    print(f"Found {len(article_links)} articles")

    for link in article_links:
        article_url = link.get("href")
        if article_url:
            scrape_article(article_url, category_folder)
            time.sleep(1)  # polite delay


# =========================
# ZIP
# =========================
def zip_results():
    if os.path.exists(f"{ZIP_NAME}.zip"):
        os.remove(f"{ZIP_NAME}.zip")

    shutil.make_archive(ZIP_NAME, "zip", BASE_FOLDER)
    print(f"\n📦 ZIP created: {ZIP_NAME}.zip")


# =========================
# MAIN
# =========================
def main():
    print("🔎 Fetching Health Topic categories...\n")

    response = fetch_url(MAIN_PAGE, headers)
    if response is None:
        return

    soup = BeautifulSoup(response.text, "html.parser")

    categories = soup.select("a[href*='health-topics-category']")
    seen = set()
    unique_categories = []

    for cat in categories:
        name = cat.get_text(strip=True)
        url = cat.get("href")
        if url and url not in seen:
            seen.add(url)
            unique_categories.append((name, url))

    print(f"Total categories found: {len(unique_categories)}")

    for name, url in unique_categories:
        scrape_category(name, url)

    zip_results()
    print("\n✅ ALL categories scraped successfully")


if __name__ == "__main__":
    main()
