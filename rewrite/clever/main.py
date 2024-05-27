from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime

from database.database import ORM, UrlRepo, CategoryRepo
from database.models import Product, Category


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


async def parse_clever(orm):
    while True:
        print("Start parse")
        category_urls = await orm.url_repo.select_urls(1)
        for category_url in category_urls:
            print(f"Category {category_url.url} parse")
            driver.get(category_url.url)
            time.sleep(10)

            try:
                category_name_element = driver.find_element(By.CLASS_NAME, 'description-sm')
                category_name = category_name_element.text.strip()
            except NoSuchElementException:
                category_name = "Категория не найдена"

            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(10)

                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            product_cards = driver.find_elements(By.CLASS_NAME, 'product-card')
            for card in product_cards:
                # print("Product add")
                product = Product()
                product.name = card.find_element(By.CLASS_NAME, "product-card-title").text.strip()
                product.price = card.find_element(By.CLASS_NAME, "text-sm").text.strip()
                product.image_url = card.find_element(By.TAG_NAME, "img").get_attribute("src")
                product.link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

                category = Category()
                category.name = category_name
                category.site_id = 1
                product.category_id = (await orm.category_repo.get_category(category))
                await orm.product_repo.insert_or_update_product(product)
        print(f"Start pause - {(seconds := 300)} sec")
        time.sleep(seconds)
