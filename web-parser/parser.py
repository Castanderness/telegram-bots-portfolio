"""
Universal web parser template.
Sell this as a service on Fiverr — customize target URL and selectors per client.
"""

import csv
import json
import time
import random
import logging
from dataclasses import dataclass, asdict
from typing import Optional
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class Product:
    title: str
    price: str
    url: str
    description: Optional[str] = None
    image: Optional[str] = None


def fetch_page(url: str, retries: int = 3) -> Optional[BeautifulSoup]:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:
            logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(random.uniform(2, 5))
    return None


def parse_product_list(base_url: str, pages: int = 5) -> list[Product]:
    """
    CUSTOMIZE THIS per client:
    - Change selectors (.product-card, .price, etc.)
    - Change pagination logic
    - Add filters
    """
    products = []

    for page in range(1, pages + 1):
        url = f"{base_url}?page={page}"
        logging.info(f"Parsing page {page}: {url}")

        soup = fetch_page(url)
        if not soup:
            continue

        # ---- CUSTOMIZE SELECTORS HERE ----
        cards = soup.select(".product-card")  # Change this selector

        for card in cards:
            title_el = card.select_one(".product-title")
            price_el = card.select_one(".product-price")
            link_el = card.select_one("a")
            img_el = card.select_one("img")

            if not title_el or not price_el:
                continue

            products.append(Product(
                title=title_el.get_text(strip=True),
                price=price_el.get_text(strip=True),
                url=link_el["href"] if link_el else "",
                image=img_el.get("src") if img_el else None,
            ))

        # Polite delay between pages
        time.sleep(random.uniform(1.5, 3.5))

    logging.info(f"Total products parsed: {len(products)}")
    return products


def save_to_csv(products: list[Product], filename: str = "output.csv"):
    if not products:
        logging.warning("No products to save")
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=asdict(products[0]).keys())
        writer.writeheader()
        writer.writerows(asdict(p) for p in products)
    logging.info(f"Saved to {filename}")


def save_to_json(products: list[Product], filename: str = "output.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([asdict(p) for p in products], f, ensure_ascii=False, indent=2)
    logging.info(f"Saved to {filename}")


if __name__ == "__main__":
    # ---- CHANGE THIS URL ----
    TARGET_URL = "https://example.com/products"
    PAGES = 10

    products = parse_product_list(TARGET_URL, pages=PAGES)
    save_to_csv(products, "output.csv")
    save_to_json(products, "output.json")
