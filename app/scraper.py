"""
Scraper : va chercher l'inventaire en direct sur hyundaistraymond.com
et retourne une liste de véhicules avec tous les champs pour Meta.
"""
import re, json, logging
from urllib.request import Request, urlopen
from urllib.error import URLError

BASE_URL = "https://www.hyundaistraymond.com"
SEARCH_URL = f"{BASE_URL}/occasion/recherche.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "fr-CA,fr;q=0.9",
}

log = logging.getLogger(__name__)


def fetch(url: str) -> str:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_vehicles(html: str) -> list:
    """Extraire les véhicules depuis les blocs schema.org Product."""
    vehicles = []

    schema_blocks = re.findall(
        r'\{"@context":"https:\\/\\/schema\.org\\/","@type":"Product".*?\}', html
    )
    slug_map = {
        vid: slug
        for slug, vid in re.findall(r'/occasion/([^"\']+?-id(\d+)\.html)', html)
    }

    # Also extract extra info: prix, km, stock, couleur, transmission
    # D2C Media embeds these in data attributes or JS
    # Extract from visible card text blocks keyed by d2c id
    # Pattern: data-id="13729319" or similar
    data_attrs = {}
    for block in re.finditer(
        r'data-vehicleid=["\'](\d+)["\'][^>]*>.*?</[a-z]+>',
        html, re.DOTALL
    ):
        pass  # placeholder for richer scraping if needed

    for block in schema_blocks:
        block = block.replace("\\/", "/")
        try:
            data = json.loads(block)
        except Exception:
            continue

        name  = data.get("name", "").strip()
        sku   = str(data.get("sku", ""))
        imgs  = data.get("image", [])
        image = imgs[0] if isinstance(imgs, list) and imgs else str(imgs)

        parts = name.split()
        if len(parts) < 3:
            continue
        try:
            year = int(parts[-1])
        except ValueError:
            continue
        make  = parts[0]
        model = " ".join(parts[1:-1])

        slug  = slug_map.get(sku, "")
        link  = f"{BASE_URL}/occasion/{slug}" if slug else f"{BASE_URL}/occasion/recherche.html"

        vehicles.append({
            "d2c_id": sku,
            "make":   make,
            "model":  model,
            "year":   year,
            "image":  image,
            "link":   link,
        })

    return vehicles


def get_all_vehicles() -> list:
    """Scrape toutes les pages de l'inventaire d'occasion."""
    all_vehicles = []
    seen_ids = set()
    page = 1

    while True:
        url = SEARCH_URL if page == 1 else f"{SEARCH_URL}?p={page}"
        log.info(f"Scraping page {page}: {url}")
        try:
            html = fetch(url)
        except URLError as e:
            log.error(f"Erreur fetch page {page}: {e}")
            break

        vehicles = parse_vehicles(html)
        if not vehicles:
            log.info(f"Page {page}: aucun véhicule — fin")
            break

        new = [v for v in vehicles if v["d2c_id"] not in seen_ids]
        if not new:
            log.info(f"Page {page}: tous déjà vus — fin")
            break

        for v in new:
            seen_ids.add(v["d2c_id"])
        all_vehicles.extend(new)
        log.info(f"Page {page}: +{len(new)} véhicules (total: {len(all_vehicles)})")

        if len(vehicles) < 12:
            break
        page += 1

    return all_vehicles

