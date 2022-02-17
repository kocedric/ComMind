# import datetime
# import time
#
#
# class Scraper:
#     """
#     Permet de scraper les informations présents sur le site indiqué
#     """
#
#     def __init__(self, mongodb_client, bot_scraper):
#         self.mongodb_client = mongodb_client
#         self.bot_scraper = bot_scraper
#
#     def scrapeCategoryUrls(self):
#         """
#         Nous permet de scraper les urls des produits present dans la catégorie et de les sauvegardés dans MongoDB
#         """
#
#         category_urls = self.mongodb_client["amazon"]["category_urls"].find({})
#         for category_url in category_urls:
#             if category_url["scrape"] is True:
#                 print("Url à scraper (cat):", category_url["url"], "\n")
#
#                 product_urls = self.bot_scraper.getProductUrls(category_url["url"])
#
#                 # Upsert
#                 for product_url in product_urls:
#                     print("product", product_url)
#                     self.mongodb_client["amazon"]["product_urls"].update({"url": product_url},
#                                                                          {"$set": {"url": product_url}},
#                                                                          upsert=True)
#
#                 # Update
#                 self.mongodb_client["amazon"]["category_urls"].update({"url": category_url["url"]}, {"$set": {
#                     'scrape': False
#                 }})
#                 time.sleep(2)
#
#     def scrapeProductData(self):
#         """
#         Nous permet de recupérer les informations liés au produit et les stoke dans une base de donnée MongoDB
#         """
#
#         # Query MongoDB pour récupérer les liens à scraper
#         product_urls = self.mongodb_client["amazon"]["product_urls"].find({
#             "$or": [
#                 {"updated_at": None},
#                 # On ne scrape un document que 15 minutes après l'avoir déja fait
#                 # Vous pouvez augmenter cette valeur biensur
#                 # Il vaut mieux éviter de spam Amazon de requetes sinon il risque de bloquer l'ip
#                 {"updated_at": {"$lte": datetime.datetime.now() - datetime.timedelta(minutes=15)}}
#             ]
#         })
#
#         for product_url in product_urls:
#             print("Url à scraper:", product_url["url"], "\n")
#             data, reviews = self.bot_scraper.getProductData(product_url["url"])
#
#             # Upsert
#             self.mongodb_client["amazon"]["product_data"].update({"url": product_url['url']}, {"$set": data},
#                                                                  upsert=True)
#
#             if reviews is not None:
#                 # Upsert
#                 self.mongodb_client["amazon"]["product_reviews"].update({"product_url": reviews['product_url']},
#                                                                         {"$set": reviews},
#                                                                         upsert=True)
#
#             # Update
#             self.mongodb_client["amazon"]["product_urls"].update({"url": product_url["url"]}, {"$set": {
#                 'updated_at': datetime.datetime.now()
#             }})
#
#         # pause de 2 secondes
#         time.sleep(2)
