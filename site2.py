import os
import time
import requests
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

# ============================================================
# CONFIG
# ============================================================

BASE_URL = "https://www.greenmedinfo.com"
START_PAGE = "https://www.greenmedinfo.com/gmi-blogs-popular"

OUTPUT_FOLDER = "articles_for_site2"
ZIP_NAME = "articles_for_site2"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

REQUEST_DELAY = 1  # polite delay between requests

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ============================================================
# SAFE REQUEST HELPER
# ============================================================

def fetch_url(url, retries=3, timeout=30):
    """
    Safely fetch a URL with retries.
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"⏳ Retry {attempt}/{retries} → {url}")
            print(f"   Error: {e}")
            time.sleep(3)

    print(f"❌ Failed permanently → {url}")
    return None


def slug_from_url(url: str) -> str:
    """
    Extract filename-safe slug from article URL.
    """
    return url.rstrip("/").split("/")[-1]


# ============================================================
# HTML → MARKDOWN CONVERTER
# ============================================================

def html_to_markdown(content_div: BeautifulSoup) -> str:
    """
    Convert GreenMedInfo article HTML body to Markdown.
    """
    md = []

    allowed_tags = [
        "h1", "h2", "h3", "h4", "h5", "h6",
        "p", "span", "br", "hr",
        "strong", "b", "em", "i", "u",
        "ul", "ol", "li",
        "blockquote",
        "table", "thead", "tbody", "tr", "th", "td",
        "img", "figure", "figcaption",
        "pre", "code",
        "a",
        "div"
    ]

    for el in content_div.find_all(allowed_tags, recursive=True):

        # ---------------- HEADINGS ----------------
        if el.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = "#" * int(el.name[1])
            text = el.get_text(strip=True)
            if text:
                md.append(f"{level} {text}\n")

        # ---------------- PARAGRAPHS ----------------
        elif el.name in ["p", "span"]:
            text = el.get_text(" ", strip=True)
            if text and text != "\xa0":
                md.append(f"{text}\n")

        # ---------------- LISTS ----------------
        elif el.name in ["ul", "ol"]:
            for li in el.find_all("li", recursive=False):
                text = li.get_text(" ", strip=True)
                if text:
                    md.append(f"- {text}")
            md.append("")

        # ---------------- BLOCKQUOTE ----------------
        elif el.name == "blockquote":
            text = el.get_text(" ", strip=True)
            if text:
                md.append(f"> {text}\n")

        # ---------------- TABLE ----------------
        elif el.name == "table":
            md.append("")
            for row in el.find_all("tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    left = cells[0].get_text(" ", strip=True)
                    right = cells[1].get_text(" ", strip=True)
                    if left and right:
                        md.append(f"- **{left}** {right}")
            md.append("")

        # ---------------- IMAGE ----------------
        elif el.name == "img":
            src = el.get("src")
            alt = el.get("alt", "")
            if src:
                md.append(f"![{alt}]({urljoin(BASE_URL, src)})\n")

        # ---------------- CODE ----------------
        elif el.name == "pre":
            code = el.get_text()
            if code.strip():
                md.append(f"```\n{code}\n```\n")

        elif el.name == "code":
            text = el.get_text(strip=True)
            if text:
                md.append(f"`{text}`")

        # ---------------- LINKS ----------------
        elif el.name == "a":
            href = el.get("href")
            text = el.get_text(strip=True)
            if href and text:
                md.append(f"[{text}]({urljoin(BASE_URL, href)})")

    return "\n".join(md).strip()


# ============================================================
# ARTICLE SCRAPER
# ============================================================

def scrape_article(article_url: str):
    """
    Scrape a single GreenMedInfo article and save as Markdown.
    """
    print(f"   🔍 Article → {article_url}")

    response = fetch_url(article_url)
    if not response:
        return

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.select_one("div.field-title h1")
    content_div = soup.select_one("div.field-body")

    if not title_tag or not content_div:
        print("   ⚠️ Skipped (missing title/body)")
        return

    title = title_tag.get_text(strip=True)
    slug = slug_from_url(article_url)
    file_path = os.path.join(OUTPUT_FOLDER, f"{slug}.md")

    body_md = html_to_markdown(content_div)

    # Skip member-only / empty pages
    if len(body_md) < 300:
        print("   ⚠️ Skipped (low content / member-only)")
        return

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"Source: {article_url}\n\n")
        f.write(body_md)

    print(f"   ✅ Saved → {slug}.md")


# ============================================================
# PAGINATION HELPERS
# ============================================================

def get_last_page(soup: BeautifulSoup) -> int:
    """
    Extract last pagination page number.
    """
    last = soup.select_one("li.pager-last a")
    if not last:
        return 0

    parsed = urlparse(last.get("href"))
    return int(parse_qs(parsed.query).get("page", [0])[0])


# ============================================================
# MAIN SCRAPER (ALL PAGES)
# ============================================================

def scrape_all_pages():
    """
    Scrape all paginated popular blog pages.
    """
    print("🔎 Fetching first page...")

    first_response = fetch_url(START_PAGE)
    if not first_response:
        return

    soup = BeautifulSoup(first_response.text, "html.parser")
    last_page = get_last_page(soup)

    print(f"📄 Total pages detected: {last_page + 1}\n")

    seen_articles = set()

    for page in range(0, last_page + 1):
        page_url = f"{START_PAGE}?page={page}"
        print(f"\n📄 Page {page + 1}/{last_page + 1}")
        print(f"   URL → {page_url}")

        response = fetch_url(page_url)
        if not response:
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # ✅ Correct selector based on provided DOM
        article_links = soup.select("div.views-field-title a")

        print(f"   🔗 Articles found: {len(article_links)}")

        for a in article_links:
            href = a.get("href")
            if not href:
                continue

            full_url = urljoin(BASE_URL, href)

            if full_url in seen_articles:
                continue

            seen_articles.add(full_url)
            scrape_article(full_url)
            time.sleep(REQUEST_DELAY)


# ============================================================
# ZIP RESULTS
# ============================================================

def zip_results():
    """
    Zip all scraped markdown files.
    """
    zip_path = f"{ZIP_NAME}.zip"

    if os.path.exists(zip_path):
        os.remove(zip_path)

    shutil.make_archive(ZIP_NAME, "zip", OUTPUT_FOLDER)
    print(f"\n📦 ZIP created → {zip_path}")


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    print("\n🚀 GreenMedInfo Blog Scraper Started\n")
    scrape_all_pages()
    zip_results()
    print("\n✅ ALL ARTICLES SCRAPED SUCCESSFULLY\n")


if __name__ == "__main__":
    main()
