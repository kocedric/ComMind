import os

from dotenv import load_dotenv
from pymongo import MongoClient

from site_bot import AmazonBot

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
    raise e from e

# Initialisation de la classe AmazonBot
bot = AmazonBot(mongodb_client=client)
# Lancement du Scraping

bot.scrapeCategoryUrls()
bot.scrapeProductData()