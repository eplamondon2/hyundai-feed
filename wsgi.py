from app.main import app

# Ne pas charger l'inventaire au démarrage — il se chargera
# à la première requête /feed.csv pour éviter le timeout Railway.
