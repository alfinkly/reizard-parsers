from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from rewrite.database.database import ORM
from rewrite.database.models import Product, Category

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


async def parse_page(orm, category_url, category_name):
    driver.get(category_url)
    products = []
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.product-item.product-card'))
        )
    except TimeoutException:
        print("Timed out waiting for page to load")
        return

    # Получение исходного кода страницы после загрузки
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Парсинг элементов страницы
    product_cards = soup.find_all('article', class_='product-item product-card')

    for card in product_cards:
        product = Product()
        product.name = card.find('a', class_='product-card__title').text.strip()
        product.price = card.find('span', class_='price--wrapper').text.strip()
        product.image_url = card.find('img', class_='product-card__img').get('data-src')
        product.link = 'https://arbuz.kz' + card.find('a', class_='product-card__link').get('href')

        category = Category()
        category.name = category_name
        category.site_id = 2
        product.category_id = (await orm.category_repo.get_category(category))
        await orm.product_repo.insert_or_update_product(product)
        products.append(product)


async def parse_arbuz(orm: ORM):
    while True:
        category_urls = await orm.url_repo.select_urls(2)
        for url in category_urls:
            base_url_template = url[1] + '#/?%5B%7B%22slug%22%3A%22page%22,%22value%22%3A{}%2C%22component%22%3A%22' \
                                      'pagination%22%7D%5D'
            page_url = base_url_template.format(1)
            driver.get(page_url)
            time.sleep(2)
            page_buttons = driver.find_elements(By.XPATH,
                                                '/html/body/div[1]/main/section/div/section/div[2]/div[6]/nav/ul/*')
            category_name = driver.find_element(By.XPATH,
                                                '/html/body/div[1]/main/section/div/div[1]/nav/div/div/a').text

            for page_number in range(1, int(page_buttons[-2].text) + 1):
                page_url = base_url_template.format(page_number)

                driver.get(page_url)
                print(page_url)
                time.sleep(5)

                driver.execute_script("window.location.reload();")
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.product-item.product-card'))
                    )
                    await parse_page(orm, page_url, category_name)
                except TimeoutException:
                    continue

        time.sleep(300)
