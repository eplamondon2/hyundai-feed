"""
Scraper : lit le JSON d'inventaire D2C Media directement.
Valeurs formatées selon les specs Meta Commerce Manager.
"""
import json, logging, re
from urllib.request import Request, urlopen
from urllib.error import URLError

JSON_URL = "https://www.hyundaistraymond.com/js/json/chatboost/inventory/inventory-index.json"
BASE_URL  = "https://www.hyundaistraymond.com"
DEALER_ADDRESS = "484 Côte Joyeuse, Saint-Raymond, QC G3L 4A7, Canada"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "fr-CA,fr;q=0.9",
}

BODY_STYLE_MAP = {
    "suv": "SUV", "sedan": "Sedan", "truck": "Truck",
    "hatchback": "Hatchback", "coupe": "Coupe",
    "minivan": "Minivan", "van": "Minivan",
    "wagon": "Wagon", "convertible": "Convertible",
}

TRANS_MAP = {
    "automatique": "AUTOMATIC", "automatic": "AUTOMATIC",
    "manuelle": "MANUAL", "manual": "MANUAL",
    "man": "MANUAL", "auto": "AUTOMATIC",
}

log = logging.getLogger(__name__)


def fetch_json() -> list:
    req = Request(JSON_URL, headers=HEADERS)
    with urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def clean_image(url: str) -> str:
    if not url:
        return ""
    url = re.sub(r'(https?://[^/]+)//', r'\1/', url)
    return url


def fix_link(link: str, make: str, model: str, is_new: bool) -> str:
    """Corrige les liens pour qu'ils pointent vers le bon domaine."""
    if not link or "hyundaistraymond.com" not in link:
        return f"{BASE_URL}/occasion/recherche.html"
    # Véhicules usagés
    link = link.replace("/used/", "/occasion/")
    # Véhicules neufs : remplacer /new/inventory/ par /neuf/
    if "/new/inventory/" in link or "/new/" in link:
        make_slug  = make.strip().replace(" ", "-")
        model_slug = model.strip().replace(" ", "-")
        link = f"{BASE_URL}/neuf/{make_slug}-{model_slug}.html"
    return link


def parse_vehicle(v: dict) -> dict:
    d2c_id = str(v.get("D2C Vehicle ID", ""))
    stock  = str(v.get("stock number", d2c_id)).strip()
    make   = v.get("make", "")
    model  = v.get("model", "")
    year   = v.get("year", "")
    trim   = v.get("trim", "")
    price  = str(v.get("Final price", "")).replace(",", "").replace("$", "").strip()
    btype  = v.get("Vehicle Type", "").lower()
    status = str(v.get("status", "Used"))
    trans  = str(v.get("transmission", "") or "")
    is_new = "new" in status.lower()

    odo = v.get("odometer", {})
    km  = str(odo.get("value", "")).replace(",", "").replace(" ", "")
    if not km or km == "0":
        km = "0"

    color  = v.get("color", {})
    ext_fr = color.get("exterior french", "") or color.get("exterior english", "")

    image = clean_image(v.get("main picture", ""))
    link  = fix_link(
        v.get("Vehicle Details Page (VDP)", ""),
        make, model, is_new
    )

    desc = v.get("vehicle description", "").strip()
    if not desc:
        desc = (
            f"{year} {make} {model} {trim}".strip()
            + (f", {ext_fr}" if ext_fr else "")
            + (f", {km} km" if km and km != "0" else "")
            + ". Contactez-nous au 1-844-623-0597."
        )
    desc = desc[:5000]

    trans_meta        = TRANS_MAP.get(trans.lower().strip(), "OTHER")
    availability_meta = "in stock"
    condition_meta    = "used" if not is_new else "new"
    state             = "new" if is_new else "used"

    return {
        "id":               stock,
        "title":            f"{year} {make} {model}".strip(),
        "description":      desc,
        "availability":     availability_meta,
        "condition":        condition_meta,
        "price":            f"{price} CAD" if price else "",
        "link":             link,
        "image_link":       image,
        "make":             make,
        "model":            model,
        "year":             year,
        "mileage.value":    km,
        "mileage.unit":     "KM",
        "body_style":       BODY_STYLE_MAP.get(btype, "SUV"),
        "transmission":     trans_meta,
        "exterior_color":   ext_fr,
        "vehicle_id":       stock,
        "state_of_vehicle": state,
        "address":          DEALER_ADDRESS,
    }


def get_all_vehicles() -> list:
    log.info(f"Chargement JSON: {JSON_URL}")
    try:
        raw = fetch_json()
    except URLError as e:
        log.error(f"Erreur fetch JSON: {e}")
        return []
    except json.JSONDecodeError as e:
        log.error(f"Erreur parsing JSON: {e}")
        return []

    vehicles = []
    for v in raw:
        try:
            parsed = parse_vehicle(v)
            if parsed["id"]:
                vehicles.append(parsed)
        except Exception as e:
            log.warning(f"Erreur parsing {v.get('stock number','?')}: {e}")

    log.info(f"{len(vehicles)} véhicules chargés")
    return vehicles
