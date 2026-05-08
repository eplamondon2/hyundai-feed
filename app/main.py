"""
Serveur Flask — génère le flux CSV pour Meta Commerce Manager.
Routes :
  GET /feed.csv   → flux CSV pour Meta (à fournir à Meta)
  GET /health     → statut du serveur et du cache
  GET /refresh    → force un rechargement immédiat (protégé par token)
"""
import csv, io, os, logging
from flask import Flask, Response, request, jsonify
from app.cache import get_vehicles, cache_age_minutes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)

REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN", "hyundai-straymond-2024")

META_FIELDS = [
    "id", "title", "description", "availability", "condition",
    "price", "link", "image_link", "make", "model", "year",
    "mileage.value", "mileage.unit", "body_style", "transmission",
    "exterior_color", "vehicle_id", "state_of_vehicle",
]

BODY_STYLE_MAP = {
    "berline": "Sedan", "vus": "SUV", "camion": "Truck",
    "hatchback": "Hatchback", "coupé": "Coupe", "coupe": "Coupe",
}


def vehicle_to_row(v: dict) -> dict:
    return {
        "id":              v.get("id", ""),
        "title":           v.get("title", ""),
        "description":     v.get("description", ""),
        "availability":    v.get("availability", "in stock"),
        "condition":       v.get("condition", "used"),
        "price":           v.get("price", ""),
        "link":            v.get("link", ""),
        "image_link":      v.get("image_link", ""),
        "make":            v.get("make", ""),
        "model":           v.get("model", ""),
        "year":            v.get("year", ""),
        "mileage.value":   v.get("mileage.value", ""),
        "mileage.unit":    v.get("mileage.unit", "KM"),
        "body_style":      v.get("body_style", ""),
        "transmission":    v.get("transmission", ""),
        "exterior_color":  v.get("exterior_color", ""),
        "vehicle_id":      v.get("vehicle_id", ""),
        "state_of_vehicle": v.get("state_of_vehicle", "used"),
    }


@app.route("/feed.csv")
def feed_csv():
    """Flux CSV pour Meta Commerce Manager."""
    vehicles = get_vehicles()
    if not vehicles:
        return Response("Aucun véhicule disponible", status=503)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=META_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for v in vehicles:
        writer.writerow(vehicle_to_row(v))

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="meta_inventory.csv"'},
    )


@app.route("/health")
def health():
    """Healthcheck léger — ne déclenche PAS de scraping."""
    vehicles = _cache_peek()
    return jsonify({
        "status": "ok",
        "vehicles_in_cache": len(vehicles),
        "cache_age_minutes": cache_age_minutes(),
    }), 200


@app.route("/refresh")
def refresh():
    token = request.args.get("token", "")
    if token != REFRESH_TOKEN:
        return jsonify({"error": "Token invalide"}), 403
    vehicles = get_vehicles(force=True)
    return jsonify({"status": "ok", "vehicles_refreshed": len(vehicles)})


def _cache_peek():
    """Retourne le cache sans déclencher de refresh."""
    from app.cache import _cache
    return _cache["vehicles"]
@app.route("/debug")
def debug():
    import urllib.request
    url = "https://www.hyundaistraymond.com/js/json/chatboost/inventory/inventory-index.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read().decode("utf-8")
            import json
            parsed = json.loads(data)
            return jsonify({"status": "ok", "vehicles_found": len(parsed), "first": parsed[0].get("make","?") if parsed else "none"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    log.info("Chargement initial de l'inventaire...")
    get_vehicles()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

