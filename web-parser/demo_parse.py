"""Demo scrape of books.toscrape.com — a public sandbox site for scrapers."""
import csv, json, requests
from bs4 import BeautifulSoup

BASE = "https://books.toscrape.com/catalogue"
HEADERS = {"User-Agent": "Mozilla/5.0"}

books = []
for page in range(1, 4):  # 3 pages = 60 books
    url = f"{BASE}/page-{page}.html"
    soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=10).text, "lxml")
    for article in soup.select("article.product_pod"):
        books.append({
            "title":  article.select_one("h3 a")["title"],
            "price":  article.select_one(".price_color").text.strip(),
            "rating": article.select_one("p.star-rating")["class"][1],
            "stock":  article.select_one(".availability").text.strip(),
        })

with open("demo_books.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["title","price","rating","stock"])
    w.writeheader(); w.writerows(books)

with open("demo_books.json", "w", encoding="utf-8") as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print(f"Scraped {len(books)} books -> demo_books.csv + demo_books.json")
for b in books[:5]:
    print(f"  {b['title'][:45]:<45} {b['price']}  {b['rating']}")
