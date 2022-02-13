import time
import datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver


class AmazonBot:

    def __init__(self, mongodb_client, server_smtp):
        self.amazon_header = {
            'authority': 'www.amazon.fr',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-gpc': '1',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.mongodb_client = mongodb_client
        self.server_smtp = server_smtp
        # Ajouter ici le chemin vers chromedriver
        # self.driver = webdriver.Chrome(executable_path=r"C:\Users\cedri\Documents\chromedriver_win32\chromedriver.exe")
        # ou bien autre astuce faites un pip install webdriver-manager
        # et a la place du chemin mettez ChromeDriverManager().install()
        # si vous préférez la seconde solution enlever les commentaires des deux prochaines lignes
        # et commentez la ligne 29
        options = webdriver.ChromeOptions()
        # to supress the error messages/logs
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        from webdriver_manager.chrome import ChromeDriverManager
        self.driver = webdriver.Chrome(executable_path=ChromeDriverManager().install())

    def get_product_title(self, soup):
        try:
            return soup.find('span', {'id': 'productTitle'}).get_text().strip()
        except:
            return None

    def get_product_rating(self, soup):
        try:
            div_avg_cust_reviews = soup.find('div', {'id': 'averageCustomerReviews'})
            rating = div_avg_cust_reviews.find('span', {'class': 'a-icon-alt'}).get_text().strip().split()[0]
            return float(rating.replace(',', '.'))
        except:
            return None

    def get_product_nb_reviewers(self, soup):
        try:
            nb_reviewers = soup.find('span', {'id': 'acrCustomerReviewText'}).get_text().strip()
            return int(''.join(nb_reviewers.split()[:-1]))
        except:
            return None

    def get_product_price(self, soup):
        try:
            price = soup.find('span', {
                'class': 'a-price aok-align-center priceToPay',
                'data-a-color': 'base'}) \
                .find('span', {'class': 'a-offscreen'}) \
                .get_text().strip()
            return float(price.strip().replace(',', '.')[:-1])
        except:
            return None

    def get_product_link_reviewers(self, soup):
        try:
            reviewers_link = soup.find('a', {'data-hook': 'see-all-reviews-link-foot'})
            return f"https://www.amazon.fr{reviewers_link['href']}"
        except:
            return None

    def get_product_urls(self, category_url):
        self.driver.get(category_url)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        try:
            products_links = soup.find_all('a', {'class': 'a-link-normal s-no-outline'}, limit=10)
            products_urls = [f"https://www.amazon.fr{product_link['href']}" for product_link in products_links]
            return products_urls
        except:
            return None

    def get_product_reviewers_title(self, soup):
        try:
            titles = soup.find_all('a', {'data-hook': 'review-title'}, limit=10)
            return [title.find('span').get_text().strip() for title in titles]
        except:
            return None

    def get_product_reviewers_date(self, soup):
        try:
            dates = soup.find_all('span', {'data-hook': 'review-date'}, limit=10)
            return [date.get_text().strip() for date in dates]
        except:
            return None

    def get_product_reviewers_body(self, soup):
        try:
            contents = soup.find_all('span', {'data-hook': 'review-body'}, limit=10)
            return [content.find('span').get_text().strip() for content in contents]
        except:
            return None

    def get_product_reviewers(self, review_url, product_title, product_url):
        try:
            self.driver.get(review_url)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # review_title = self.get_product_reviewers_title(soup)
            review_dates = self.get_product_reviewers_date(soup)
            region = [review_date.split()[2] for review_date in review_dates]
            date = [' '.join(date.split()[4:]) for date in review_dates]
            body = self.get_product_reviewers_body(soup)
            return {
                "product_title": product_title,
                "product_url": product_url,
                "date": date,
                "region": region,
                "body": body
            }
        except:
            return None

    def get_product_data(self, product_url):
        self.driver.get(product_url)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        # r = requests.get(product_url, headers=self.amazon_header)
        # soup = BeautifulSoup(r.content, 'html.parser')
        title = self.get_product_title(soup)
        rating = self.get_product_rating(soup)
        nb_reviewers = self.get_product_nb_reviewers(soup)
        price = self.get_product_price(soup)
        reviewers_url = self.get_product_link_reviewers(soup)
        print("review url:", reviewers_url, type(reviewers_url))
        product_reviews = self.get_product_reviewers(reviewers_url, title, product_url)
        print(f"\n{product_reviews}\n")

        data = {
            "url": product_url,
            "title": title,
            "rating": rating,
            "nb_reviewers": nb_reviewers,
            "price": price,
            "update_date": datetime.datetime.now()
        }

        return data, product_reviews

    def scrap_urls(self):
        category_urls = self.mongodb_client["amazon"]["category_urls"].find({})
        for category_url in category_urls:
            if category_url["scrape"] is True:
                print("Url à scraper (cat):", category_url["url"], "\n")

                products = self.get_product_urls(category_url["url"])

                # Upsert
                for product in products:
                    print("product", product)
                    self.mongodb_client["amazon"]["product_urls"].update({"url": product}, {"$set": {"url": product}},
                                                                         upsert=True)

                # Update
                self.mongodb_client["amazon"]["category_urls"].update({"url": category_url["url"]}, {"$set": {
                    'scrape': False
                }})

        # Query MongoDB pour récupérer les liens à scraper
        product_urls = self.mongodb_client["amazon"]["product_urls"].find({
            "$or": [
                {"updated_at": None},
                # On ne scrape un document que 15 minutes après l'avoir déja fait
                # Vous pouvez augmenter cette valeur biensur
                # Il vaut mieux éviter de spam Amazon de requetes sinon il risque de bloquer l'ip
                {"updated_at": {"$lte": datetime.datetime.now() - datetime.timedelta(minutes=15)}}
            ]
        })

        for product_url in product_urls:
            print("Url à scraper:", product_url["url"], "\n")
            data, reviews = self.get_product_data(product_url["url"])

            # Upsert
            self.mongodb_client["amazon"]["product_data"].update({"url": product_url['url']}, {"$set": data},
                                                                 upsert=True)

            if reviews is not None:
                # Upsert
                self.mongodb_client["amazon"]["product_reviews"].update({"product_url": reviews['product_url']},
                                                                        {"$set": reviews},
                                                                        upsert=True)

            # Update
            self.mongodb_client["amazon"]["product_urls"].update({"url": product_url["url"]}, {"$set": {
                'updated_at': datetime.datetime.now()
            }})

            ## Dernier prix enregistrer pour un produit
            # try:
            #    last_product_price = self.mongodb_client["amazon"]["product_prices"].find(
            #        {"url": data['url']}).sort([('created_at', -1)]).next()
            # except:
            #    last_product_price = None

            ## On insert directement si aucun prix n'existe pour le produit en question
            # if last_product_price is None:
            #    # Insert
            #    self.mongodb_client["amazon"]["product_prices"].insert({
            #        "url": product_url["url"],
            #        "price": data["price"],
            #        "created_at": datetime.datetime.now()
            #    })
            ## S'il existe un précédent prix au produit et que celui-ci est différent
            ## du prix que l'on vient de récupérer
            # elif last_product_price is not None and last_product_price['price'] != data['price']:
            #    # Insert
            #    self.mongodb_client["amazon"]["product_prices"].insert({
            #        "url": product_url["url"],
            #        "price": data["price"],
            #        "created_at": datetime.datetime.now()
            #    })

            #    # On check le type
            #    if (type(data["price"]) is int or type(data['price']) is float) and \
            #            (type(last_product_price["price"]) is int or type(last_product_price["price"]) is float):

            #        # On calcule la différence entre l'ancien et le nouveau prix
            #        diff_price_percentage = (1 - data["price"] / last_product_price["price"]) * 100

            #        # S'il y a une baisse du prix on envoie un email
            #        if diff_price_percentage > 0:
            #            message = """
            #            Diminution du prix de %s%% pour le produit %s.
            #            Précédent prix: %s.
            #            Nouveau prix: %s.
            #            """ % (
            #                diff_price_percentage,
            #                product_url["url"],
            #                last_product_price["price"],
            #                data["price"]
            #            )
            #            # On encode ici le message car j'y ai ajouté un caractère spécial le %
            #            message = message.encode("utf-8")
            #            # Ajouter l'email d'envoi et de réception du message
            #            self.server_smtp.sendmail("specialtorrent02@gmail.com", "specialtorrent02@gmail.com", message)
        # pause de 2 secondes
        time.sleep(2)