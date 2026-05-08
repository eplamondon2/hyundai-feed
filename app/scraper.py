"""
Scraper : lit le JSON d'inventaire D2C Media directement.
URL stable, pas de JavaScript nécessaire, données complètes.
"""
import json, logging
from urllib.request import Request, urlopen
from urllib.error import URLError

JSON_URL = "https://www.hyundaistraymond.com/js/json/chatboost/inventory/inventory-index.json"
BASE_URL  = "https://www.hyundaistraymond.com"

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

log = logging.getLogger(__name__)


def fetch_json() -> list:
    req = Request(JSON_URL, headers=HEADERS)
    with urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_vehicle(v: dict) -> dict:
    d2c_id = str(v.get("D2C Vehicle ID", ""))
    stock  = str(v.get("stock number", d2c_id))
    make   = v.get("make", "")
    model  = v.get("model", "")
    year   = v.get("year", "")
    trim   = v.get("trim", "")
    price  = v.get("Final price", "")
    btype  = v.get("Vehicle Type", "").lower()
    status = v.get("status", "Used")

    odo  = v.get("odometer", {})
    km   = str(odo.get("value", "")).replace(",", "")

    color  = v.get("color", {})
    ext_fr = color.get("exterior french", "") or color.get("exterior english", "")

    image = v.get("main picture", "")
    link  = v.get("Vehicle Details Page (VDP)", f"{BASE_URL}/occasion/recherche.html")
    link  = link.replace("/used/", "/occasion/")

    desc = v.get("vehicle description", "").strip()
    if not desc:
        desc = (
            f"{year} {make} {model} {trim}".strip()
            + (f", {ext_fr}" if ext_fr else "")
            + (f", {km} km" if km else "")
            + ". Contactez-nous au 1-844-623-0597."
        )
    desc = desc[:5000]

    return {
        "id":               stock,
        "title":            f"{year} {make} {model}".strip(),
        "description":      desc,
        "availability":     "in stock",
        "condition":        "used" if "used" in status.lower() else "new",
        "price":            f"{price} CAD" if price else "",
        "link":             link,
        "image_link":       image,
        "make":             make,
        "model":            model,
        "year":             year,
        "mileage.value":    km,
        "mileage.unit":     "KM",
        "body_style":       BODY_STYLE_MAP.get(btype, "SUV"),
        "transmission":     "",
        "exterior_color":   ext_fr,
        "vehicle_id":       stock,
        "state_of_vehicle": "used" if "used" in status.lower() else "new",
        "vin":              v.get("vin", ""),
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
