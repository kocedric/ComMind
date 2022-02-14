# Import des librairies
import os

from dotenv import load_dotenv
from pymongo import MongoClient

from site_bot import AmazonBot
from scraper import Scraper

# Chargement des variables d'environnement se trouvant dans le fichier .env
load_dotenv()

# Connexion à la base de donnée MongoDB
try:
    client = MongoClient(
        "mongodb+srv://" + os.getenv("MONGODB_USERNAME") +
        ":" + os.getenv("MONGODB_PASSWORD") + "@" + os.getenv("MONGODB_DOMAIN") +
        "/" + os.getenv("MONGODB_DBNAME") + "?retryWrites=true&w=majority"
    )
    client.server_info()
except Exception as e:
    raise e

# Initialisation de la classe AmazonBot
bot = AmazonBot()
# Lancement du Scraping

scraper = Scraper(mongodb_client=client, bot_scraper=bot)
scraper.scrape_category_urls()
scraper.scrape_product_data()
