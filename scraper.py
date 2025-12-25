import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

BASE_URL = "https://www.westonaprice.org"
MAIN_PAGE = "https://www.westonaprice.org/health-topics/"
BASE_FOLDER = "articles"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

os.makedirs(BASE_FOLDER, exist_ok=True)

def slug_from_url(url):
    return url.rstrip("/").split("/")[-1]

def scrape_article(article_url, category_folder):
    response = requests.get(article_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1")
    content = soup.select_one("div.entry-content")

    if not title_tag or not content:
        print(f"⚠️ Skipping article (no content): {article_url}")
        return

    title = title_tag.get_text(strip=True)
    slug = slug_from_url(article_url)
    file_path = os.path.join(category_folder, f"{slug}.md")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"Source: {article_url}\n\n")
        f.write(content.get_text("\n", strip=True))

    print(f"   ✔ Saved: {slug}.md")

def scrape_category(name, url):
    category_slug = slug_from_url(url)
    category_folder = os.path.join(BASE_FOLDER, category_slug)

    os.makedirs(category_folder, exist_ok=True)
    print(f"\n📂 Category: {name}")
    print(f"Folder created: {category_folder}")

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    article_links = soup.select("main.content h5 a")
    print(f"Found {len(article_links)} articles")

    for link in article_links:
        article_url = link["href"]
        scrape_article(article_url, category_folder)

def main():
    print("🔎 Fetching Health Topic categories...\n")

    response = requests.get(MAIN_PAGE, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    categories = soup.select("a[href*='health-topics-category']")

    seen = set()
    unique_categories = []

    for cat in categories:
        name = cat.get_text(strip=True)
        url = cat["href"]

        if url not in seen:
            seen.add(url)
            unique_categories.append((name, url))

    print(f"Total categories found: {len(unique_categories)}")

    for name, url in unique_categories:
        scrape_category(name, url)

    print("\n✅ ALL categories scraped successfully")

if __name__ == "__main__":
    main()
