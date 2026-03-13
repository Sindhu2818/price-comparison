import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-IN,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # ── Product catalogue keyed by keyword fragments ──────────────────
        self._catalogue = {
            # Footwear
            'nike shoe': [
                ('Nike Air Max 270 Running Shoes', 8995, 12495),
                ('Nike Revolution 6 NN Sports Shoes', 3995, 5495),
                ('Nike Downshifter 12 Training Shoes', 4495, 6295),
                ('Nike React Infinity Run Flyknit 3', 11995, 15495),
                ('Nike Air Force 1 \'07 Lifestyle Shoes', 7495, 9995),
                ('Nike Pegasus 40 Road Running Shoes', 10995, 13495),
                ('Nike Flex Experience Run 11 Shoes', 3495, 4995),
                ('Nike Metcon 8 Training Shoes', 9495, 11995),
            ],
            'adidas shoe': [
                ('Adidas Ultraboost 23 Running Shoes', 12999, 17999),
                ('Adidas Stan Smith Sneakers', 6999, 9499),
                ('Adidas Samba OG Casual Shoes', 8499, 10999),
                ('Adidas NMD_R1 Lifestyle Shoes', 9999, 13499),
                ('Adidas Gazelle Indoor Shoes', 7499, 9999),
                ('Adidas Forum Low Shoes', 6499, 8499),
                ('Adidas Superstar Classic Shoes', 5999, 7999),
            ],
            'puma shoe': [
                ('Puma Softride Enzo Running Shoes', 2999, 4499),
                ('Puma RS-X³ Puzzle Sneakers', 5999, 7999),
                ('Puma Velocity NITRO 2 Running Shoes', 7999, 10499),
                ('Puma Tazon 6 FM Training Shoes', 2499, 3999),
                ('Puma Resolve Street Running Shoes', 3499, 4999),
            ],
            'shoe': [
                ('Sparx Men\'s Running Shoes', 1299, 1999),
                ('Campus Oxyfit Sports Shoes', 1499, 2199),
                ('Bata Power Walking Shoes', 1999, 2799),
                ('Red Tape Athletic Shoes', 2499, 3299),
                ('Skechers Go Walk 6 Shoes', 3999, 5499),
                ('Woodland Casual Leather Shoes', 4499, 5999),
                ('Reebok Floatride Energy 4 Shoes', 5999, 7999),
            ],
            # Phones
            'iphone': [
                ('Apple iPhone 15 (128GB) - Black', 69999, 79999),
                ('Apple iPhone 15 Plus (128GB) - Blue', 79999, 89999),
                ('Apple iPhone 15 Pro (128GB) - Natural Titanium', 134900, 144900),
                ('Apple iPhone 14 (128GB) - Midnight', 59999, 69999),
                ('Apple iPhone 13 (128GB) - Starlight', 49999, 59999),
                ('Apple iPhone 15 Pro Max (256GB)', 159900, 169900),
            ],
            'samsung phone': [
                ('Samsung Galaxy S24 Ultra 5G (256GB)', 134999, 144999),
                ('Samsung Galaxy S24+ 5G (256GB)', 99999, 109999),
                ('Samsung Galaxy A55 5G (128GB)', 34999, 39999),
                ('Samsung Galaxy M35 5G (128GB)', 19999, 23999),
                ('Samsung Galaxy F55 5G (128GB)', 26999, 30999),
            ],
            'laptop': [
                ('Dell Inspiron 15 3520 Core i5 12th Gen', 47990, 54990),
                ('HP Pavilion 15 Core i5 12th Gen 16GB RAM', 57990, 64990),
                ('Lenovo IdeaPad Slim 3 Core i5 12th Gen', 44990, 51990),
                ('ASUS VivoBook 15 Ryzen 5 5500U', 42990, 49990),
                ('Acer Aspire 5 Core i3 12th Gen', 36990, 43990),
                ('MSI Modern 14 Core i5 12th Gen', 54990, 61990),
                ('Apple MacBook Air M2 8GB 256GB', 99900, 114900),
                ('Apple MacBook Pro M3 14-inch', 168900, 184900),
            ],
            'headphone': [
                ('Sony WH-1000XM5 Wireless Noise Cancelling', 24990, 29990),
                ('Bose QuietComfort 45 Wireless Headphones', 29990, 34990),
                ('JBL Tune 770NC Wireless Headphones', 7999, 10999),
                ('Sennheiser HD 450BT Bluetooth Headphones', 9999, 12999),
                ('boAt Rockerz 450 Bluetooth Headphones', 1299, 1999),
                ('Noise One ANC Wireless Headphones', 1999, 2999),
                ('Skullcandy Crusher Evo Wireless', 12999, 15999),
            ],
            'earphone': [
                ('Sony WF-1000XM5 True Wireless Earbuds', 19990, 24990),
                ('Apple AirPods Pro (2nd Gen)', 24900, 27900),
                ('Samsung Galaxy Buds2 Pro', 13999, 16999),
                ('boAt Airdopes 141 TWS Earbuds', 999, 1499),
                ('Noise Buds VS103 Pro TWS', 1299, 1799),
                ('OnePlus Buds 3 TWS Earbuds', 4999, 6499),
                ('JBL Tune Flex TWS Earbuds', 5999, 7999),
            ],
            'watch': [
                ('Apple Watch Series 9 GPS 41mm', 41900, 44900),
                ('Samsung Galaxy Watch 6 Classic 43mm', 34999, 39999),
                ('Noise ColorFit Pro 4 Smartwatch', 1999, 2799),
                ('boAt Xtend Smartwatch', 2499, 3299),
                ('Fastrack Optimus Pro Smartwatch', 3499, 4499),
                ('Garmin Forerunner 265 GPS Watch', 44999, 49999),
                ('Titan Smart Pro Smartwatch', 2999, 3999),
            ],
            'tv': [
                ('Samsung 43" 4K Crystal UHD Smart TV', 34990, 42990),
                ('LG 43" 4K UHD webOS Smart TV', 36990, 44990),
                ('Sony Bravia 43" 4K Google TV', 44990, 52990),
                ('Mi 55" 4K Ultra HD Smart Android TV', 39990, 47990),
                ('TCL 50" 4K HDR Google TV', 29990, 36990),
            ],
            'refrigerator': [
                ('LG 260L Frost Free Double Door Refrigerator', 27990, 33990),
                ('Samsung 253L 3 Star Double Door Fridge', 24990, 30990),
                ('Whirlpool 265L 3 Star Frost Free Refrigerator', 26490, 31990),
                ('Godrej 236L 2 Star Single Door Refrigerator', 17490, 21990),
                ('Haier 258L 3 Star Double Door Refrigerator', 22990, 27990),
            ],
            'shirt': [
                ('Allen Solly Men\'s Regular Fit Formal Shirt', 1299, 1999),
                ('Van Heusen Men\'s Slim Fit Check Shirt', 1499, 2199),
                ('Raymond Men\'s Formal Cotton Shirt', 1599, 2299),
                ('Peter England Men\'s Classic Shirt', 999, 1499),
                ('Arrow Men\'s Formal Striped Shirt', 1799, 2499),
                ('Tommy Hilfiger Men\'s Casual Shirt', 2499, 3499),
            ],
            'jeans': [
                ('Levi\'s 511 Slim Fit Men\'s Jeans', 2999, 3999),
                ('Lee Men\'s Regular Fit Straight Jeans', 2499, 3299),
                ('Wrangler Men\'s Regular Fit Jeans', 1999, 2799),
                ('Pepe Jeans Men\'s Slim Fit Jeans', 2299, 3099),
                ('Spykar Men\'s Skinny Fit Jeans', 1799, 2499),
                ('Flying Machine Men\'s Slim Fit Jeans', 1999, 2699),
            ],
        }

        # Brand→image keyword mapping for Unsplash
        self._image_keywords = {
            'shoe': 'sneakers',
            'nike': 'nike+shoes',
            'adidas': 'adidas+shoes',
            'puma': 'puma+shoes',
            'iphone': 'iphone',
            'samsung': 'samsung+phone',
            'laptop': 'laptop',
            'headphone': 'headphones',
            'earphone': 'earbuds',
            'watch': 'smartwatch',
            'tv': 'television',
            'refrigerator': 'refrigerator',
            'shirt': 'shirt',
            'jeans': 'jeans',
        }

    # ─────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────

    def search_products(self, query: str, max_results: int = 20, use_real_data: bool = True):
        """Main search — tries real scraping first, falls back to smart demo."""
        logger.info(f"Searching for: '{query}'")
        results = []

        if use_real_data:
            results = self._try_real_scrape(query, max_results)

        if len(results) < 6:
            logger.info("Real scraping returned too few results — using smart demo data")
            results = self._smart_demo(query, max_results)

        # Deduplicate
        seen, unique = set(), []
        for p in results:
            key = (p['name'][:60].lower(), p['price'])
            if key not in seen:
                seen.add(key)
                unique.append(p)

        unique.sort(key=lambda x: x['price'])
        return unique[:max_results]

    def scrape_product_page(self, url):
        """Scrape a single product page for details."""
        try:
            response = self._get(url)
            if not response:
                return None
            soup = BeautifulSoup(response.content, 'html.parser')
            website = self._detect_site(url)
            details = {'website': website, 'url': url}

            for sel in ['h1', '#productTitle', '.B_NuCI', '.pdp-title', 'h1.product-title']:
                e = soup.select_one(sel)
                if e:
                    details['name'] = e.text.strip()[:200]
                    break

            for sel in ['.a-price-whole', '._30jeq3', '.price', '.product-price']:
                e = soup.select_one(sel)
                if e:
                    m = re.search(r'[\d,]+', e.text.replace('₹', '').replace(',', ''))
                    if m:
                        details['price'] = float(m.group().replace(',', ''))
                    break

            for sel in ['#landingImage', '._396cs4', 'img.product-image']:
                e = soup.select_one(sel)
                if e and e.get('src'):
                    details['image_url'] = e['src']
                    break

            details.setdefault('name', 'Product')
            details.setdefault('price', 0)
            details.setdefault('image_url', self._placeholder())
            details['availability'] = 'In Stock'
            details['delivery_date'] = self._delivery()
            return details
        except Exception as e:
            logger.error(f"Product page scrape failed: {e}")
            return None

    def update_product_prices(self, product_urls):
        updated = []
        for url in product_urls:
            try:
                data = self.scrape_product_page(url)
                if data:
                    updated.append(data)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Price update failed for {url}: {e}")
        return updated

    # ─────────────────────────────────────────────────────────────────────
    # Real scraping (best-effort)
    # ─────────────────────────────────────────────────────────────────────

    def _try_real_scrape(self, query: str, max_results: int):
        results = []
        try:
            results += self._scrape_amazon(query, max_results // 2)
        except Exception as e:
            logger.warning(f"Amazon failed: {e}")
        try:
            results += self._scrape_flipkart(query, max_results // 2)
        except Exception as e:
            logger.warning(f"Flipkart failed: {e}")
        return results

    def _scrape_amazon(self, query: str, limit: int = 10):
        url = f"https://www.amazon.in/s?k={quote_plus(query)}"
        resp = self._get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.content, 'html.parser')
        products = []
        for item in soup.select('div[data-component-type="s-search-result"]')[:limit]:
            try:
                title = item.select_one('h2 a span')
                price = item.select_one('.a-price-whole')
                img   = item.select_one('.s-image')
                link  = item.select_one('h2 a')

                if not (title and price):
                    continue

                price_val = float(re.sub(r'[^\d]', '', price.text) or 0)
                if price_val <= 0:
                    continue

                href = urljoin('https://www.amazon.in', link['href']) if link else ''
                products.append(self._build(
                    name=title.text.strip(),
                    price=price_val,
                    image=img['src'] if img else self._placeholder(),
                    url=href,
                    site='amazon',
                ))
            except Exception:
                continue
        time.sleep(1.5)
        return products

    def _scrape_flipkart(self, query: str, limit: int = 10):
        url = f"https://www.flipkart.com/search?q={quote_plus(query)}"
        resp = self._get(url)
        if not resp:
            return []
        soup = BeautifulSoup(resp.content, 'html.parser')
        products = []

        # Flipkart uses different layouts; try multiple selectors
        items = (
            soup.select('div[data-id]') or
            soup.select('div._1AtVbE') or
            soup.select('div.tUxRFH')
        )

        for item in items[:limit]:
            try:
                title = (
                    item.select_one('div._4rR01T') or
                    item.select_one('a.s1Q9rs') or
                    item.select_one('div.KzDlHZ')
                )
                price = (
                    item.select_one('div._30jeq3') or
                    item.select_one('div.Nx9bqj')
                )
                img  = item.select_one('img._396cs4') or item.select_one('img.DByuf4')
                link = item.select_one('a._1fQZEK') or item.select_one('a.s1Q9rs') or item.select_one('a.CGtC98')

                if not (title and price):
                    continue

                price_val = float(re.sub(r'[^\d]', '', price.text) or 0)
                if price_val <= 0:
                    continue

                href = urljoin('https://www.flipkart.com', link['href']) if link else ''
                products.append(self._build(
                    name=title.text.strip(),
                    price=price_val,
                    image=img['src'] if img else self._placeholder(),
                    url=href,
                    site='flipkart',
                ))
            except Exception:
                continue
        time.sleep(1.2)
        return products

    # ─────────────────────────────────────────────────────────────────────
    # Smart demo fallback  (realistic, query-matched)
    # ─────────────────────────────────────────────────────────────────────

    def _smart_demo(self, query: str, count: int = 20):
        ql = query.lower()

        # Find best matching catalogue key
        matched_key = None
        best_score = 0
        for key in self._catalogue:
            words = key.split()
            score = sum(1 for w in words if w in ql)
            if score > best_score:
                best_score = score
                matched_key = key

        # Partial word match fallback
        if not matched_key or best_score == 0:
            for key in self._catalogue:
                for word in key.split():
                    if word in ql or ql in key:
                        matched_key = key
                        break
                if matched_key:
                    break

        # Generic fallback
        if not matched_key:
            return self._generic_demo(query, count)

        templates = self._catalogue[matched_key]
        sites = ['amazon', 'flipkart', 'myntra', 'meesho', 'croma', 'reliance digital']
        products = []

        for i in range(count):
            tpl = templates[i % len(templates)]
            name, lo, hi = tpl
            price_amazon   = random.randint(lo, hi)
            price_flipkart = random.randint(int(lo * 0.95), int(hi * 0.98))

            # Amazon entry
            products.append(self._build(
                name=name,
                price=price_amazon,
                image=self._image_for(ql, i),
                url=f"https://www.amazon.in/s?k={quote_plus(name)}",
                site='amazon',
            ))

            # Flipkart entry (slightly different price)
            products.append(self._build(
                name=name,
                price=price_flipkart,
                image=self._image_for(ql, i + 100),
                url=f"https://www.flipkart.com/search?q={quote_plus(name)}",
                site='flipkart',
            ))

            if len(products) >= count:
                break

        return products[:count]

    def _generic_demo(self, query: str, count: int):
        """Fallback for queries not in catalogue — uses query name directly."""
        sites = ['amazon', 'flipkart']
        products = []
        variants = ['Standard', 'Pro', 'Plus', 'Lite', 'Premium', 'Max', 'Ultra']
        for i in range(count):
            variant = variants[i % len(variants)]
            name = f"{query.title()} {variant}"
            price = random.randint(999, 49999)
            site = sites[i % len(sites)]
            products.append(self._build(
                name=name,
                price=price,
                image=self._image_for(query.lower(), i),
                url=f"https://www.{site}.in/search?q={quote_plus(name)}",
                site=site,
            ))
        return products

    # ─────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────

    def _build(self, name, price, image, url, site):
        return {
            'name': name[:200],
            'price': round(price, 2),
            'image_url': image,
            'product_url': url,
            'website': site,
            'delivery_date': self._delivery(),
            'availability': 'In Stock' if random.random() > 0.08 else 'Out of Stock',
            'timestamp': datetime.now().isoformat(),
            'rating': round(random.uniform(3.8, 4.8), 1),
            'reviews': random.randint(120, 18000),
        }

    def _get(self, url, retries=3):
        for attempt in range(retries):
            try:
                r = self.session.get(url, timeout=12)
                r.raise_for_status()
                if any(t in r.text.lower() for t in ['captcha', 'robot', 'access denied', 'blocked']):
                    logger.warning(f"Bot detection on {url}")
                    return None
                return r
            except requests.RequestException as e:
                logger.warning(f"Request attempt {attempt+1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def _image_for(self, query_lower: str, seed: int = 0):
        """Return a product-relevant image URL using Picsum with a stable seed."""
        # Use a fixed seed so same product always gets same image
        fixed_seed = abs(hash(query_lower)) % 900 + seed % 100
        return f"https://picsum.photos/seed/{fixed_seed}/300/300"

    def _delivery(self):
        return random.choice(['Tomorrow', '1-2 days', '2-3 days', '3-5 days', '5-7 days'])

    @staticmethod
    def _placeholder():
        return f"https://picsum.photos/seed/{random.randint(1,999)}/300/300"

    @staticmethod
    def _detect_site(url: str):
        for site in ['amazon', 'flipkart', 'myntra', 'meesho']:
            if site in url:
                return site
        return 'unknown'

    # kept for backward-compat with app.py calls
    def _get_demo_data(self, query, count=10):
        return self._smart_demo(query, count)


# ── Singleton ─────────────────────────────────────────────────────────────────
scraper_instance = PriceScraper()

def get_scraper():
    return scraper_instance