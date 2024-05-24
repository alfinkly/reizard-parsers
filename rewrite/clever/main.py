from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime

from rewrite.database.database import ORM, UrlRepo, CategoryRepo
from rewrite.database.models import Product, Category

# Настройка драйвера Selenium для работы в фоновом режиме
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Добавление опции для запуска в фоновом режиме
chrome_options.add_argument(
    "--no-sandbox")  # Запуск Chrome без использования песочницы (необходимо в Docker и некоторых серверных средах)
chrome_options.add_argument(
    "--disable-dev-shm-usage")  # Отключение использования разделяемой памяти, что является хорошей практикой в серверных средах
chrome_options.add_argument(
    "--window-size=1920,1080")  # Установка размера окна, что важно для некоторых элементов страницы, требующих определённого разрешения

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Подключение к MongoDB
# client = MongoClient('mongodb+srv://umirzakdukenbaev:1@cluster0.jc3lw.mongodb.net/')
# db = client['ARBKLE']
# collection = db['KLEVER']

# category_urls = [
#     'https://clevermarket.kz/supermarket/catalog/Ovoshchi-zelen-gribi-solenya/1089',
#     'https://clevermarket.kz/supermarket/catalog/Frukti-yagodi/1090',
#     'https://clevermarket.kz/supermarket/catalog/Molochnie-produkti-yaitso/1118',
#     'https://clevermarket.kz/supermarket/catalog/Siri/1135',
#     'https://clevermarket.kz/supermarket/catalog/Maionez-sousi/1147',
#     'https://clevermarket.kz/supermarket/catalog/Khleb/1151',
#     'https://clevermarket.kz/supermarket/catalog/Vipechka/1157',
#     'https://clevermarket.kz/supermarket/catalog/Myaso-ptitsa/1162',
#     'https://clevermarket.kz/supermarket/catalog/Riba-moreprodukti-ikra/1173',
#     'https://clevermarket.kz/supermarket/catalog/Kolbasi-delikatesi/1186',
#     'https://clevermarket.kz/supermarket/catalog/Sosiski-sardelki/1198',
#     'https://clevermarket.kz/supermarket/catalog/Polufabrikati/1202',
#     'https://clevermarket.kz/supermarket/catalog/Ovoshchifrukti-zamorozhennie/1210',
#     'https://clevermarket.kz/supermarket/catalog/Morozhenoe/1213',
#     'https://clevermarket.kz/supermarket/catalog/Konservi/1215',
#     'https://clevermarket.kz/supermarket/catalog/Muka-vs-dlya-vipechki/1223',
#     'https://clevermarket.kz/supermarket/catalog/Krupi/1228',
#     'https://clevermarket.kz/supermarket/catalog/Pasta-makaroni-lapsha/1234',
#     'https://clevermarket.kz/supermarket/catalog/Med-varene-dzhemi/1240',
#     'https://clevermarket.kz/supermarket/catalog/Orekhi-sukhofrukti-semechki/1247',
#     'https://clevermarket.kz/supermarket/catalog/Konfeti-zefir-marmelad/1251',
#     'https://clevermarket.kz/supermarket/catalog/Pechene-vafli-torti/1262',
#     'https://clevermarket.kz/supermarket/catalog/Shokolad-batonchiki-pasta/1268',
#     'https://clevermarket.kz/supermarket/catalog/Chipsi-sukhariki-sneki/1274',
#     'https://clevermarket.kz/supermarket/catalog/Produkti-bistrogo-prigotovleniya/1278',
#     'https://clevermarket.kz/supermarket/catalog/Spetsii-pripravi/1282',
#     'https://clevermarket.kz/supermarket/catalog/Ketchup-tomatnaya-pasta-sousi/1288',
#     'https://clevermarket.kz/supermarket/catalog/Rastitelnie-masla/1293',
#     'https://clevermarket.kz/supermarket/catalog/Sukhie-zavtraki-khlopya-myusli/1298',
#     'https://clevermarket.kz/supermarket/catalog/Sakhar-sol/1304',
#     'https://clevermarket.kz/supermarket/catalog/Siropi/1309',
#     'https://clevermarket.kz/supermarket/catalog/Uksusi-balzamiki-dressingi/1313',
#     'https://clevermarket.kz/supermarket/catalog/Chai/1318',
#     'https://clevermarket.kz/supermarket/catalog/Kofe-kakao-sukhoe-moloko/1322',
#     'https://clevermarket.kz/supermarket/catalog/Soevie-produkti/1329',
#     'https://clevermarket.kz/supermarket/catalog/Aziatskaya-kukhnya/1332',
#     'https://clevermarket.kz/supermarket/catalog/Khumus-takhini/1340',
#     'https://clevermarket.kz/supermarket/catalog/Shampanskoe-igristie-vina/1344',
#     'https://clevermarket.kz/supermarket/catalog/Vina/1349',
#     'https://clevermarket.kz/supermarket/catalog/Pivo/1354',
#     'https://clevermarket.kz/supermarket/catalog/Krepkii-alkogol/1613',
#     'https://clevermarket.kz/supermarket/catalog/Bezalkogolnoe-shampanskoe-i-vino/1695',
#     'https://clevermarket.kz/supermarket/catalog/Soki-nektari-kompoti/1360',
#     'https://clevermarket.kz/supermarket/catalog/Voda/1364',
#     'https://clevermarket.kz/supermarket/catalog/Napitki/1369',
#     'https://clevermarket.kz/supermarket/catalog/Poleznie-napitki/1376',
#     'https://clevermarket.kz/supermarket/catalog/Siropi-sakharozameniteli/1382',
#     'https://clevermarket.kz/supermarket/catalog/Makaroni-krupi-semena-otrubi/1385',
#     'https://clevermarket.kz/supermarket/catalog/Poleznie-sladosti/1388',
#     'https://clevermarket.kz/supermarket/catalog/Khlebtsi-sneki-chipsi/1399',
#     'https://clevermarket.kz/supermarket/catalog/Maslo-pasta/1404',
# ]


async def parse_clever(orm):
    while True:
        print("Start parse")
        category_urls = await orm.url_repo.select_urls()
        for category_url in category_urls:
            print(f"Category {category_url.url} parse")
            driver.get(category_url.url)
            time.sleep(5)  # Дайте странице некоторое время, чтобы загрузиться

            try:
                category_name_element = driver.find_element(By.CLASS_NAME, 'description-sm')
                category_name = category_name_element.text.strip()
            except NoSuchElementException:
                category_name = "Категория не найдена"

            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)

                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            product_cards = driver.find_elements(By.CLASS_NAME, 'product-card')
            for card in product_cards:
                print("Product add")
                product = Product()
                product.name = card.find_element(By.CLASS_NAME, "product-card-title").text.strip()
                product.price = card.find_element(By.CLASS_NAME, "text-sm").text.strip()
                product.image_url = card.find_element(By.TAG_NAME, "img").get_attribute("src")
                product.link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

                product.category_id = (await orm.category_repo.get_category(category_name)).id
                await orm.product_repo.insert_or_update_product(product)
        print("Start pause - 5 sec")
        time.sleep(5)  # Пауза перед следующим циклом парсинга, здесь 5 минут
