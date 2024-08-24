import asyncio
import re
import time
from functools import wraps

import aiohttp
from bs4 import BeautifulSoup

BETHOWEN = "https://www.bethowen.ru"
CATALOGUE_URL = BETHOWEN + "/catalogue"
LINK = "https://www.bethowen.ru/catalogue/dogs/korma/syxoi/korm-dlya-sobak-more-dlya-srednikh-i-krupnykh-porod-s-yagnenkom-sukh/?oid=578206"
start_time = time.time()
total = []
headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.26",
    }


async def get_page(session, page):
    url = "https://www.bethowen.ru/catalogue/cats/korma/diety/korm-dlya-koshek-royal-canin-vet-diet-urinary-s-o-lp34-pri-mochekamennoy-bolezni-ptitsa/"

    async with session.get(url=url, headers=headers) as response:
        response_text = await response.text()
        soup = BeautifulSoup(response_text, 'lxml')

        city = soup.find("span", class_="ixi-header__top--region-desktop").text
        data_product_div = soup.find("div", class_="card_detail dgn-relative", attrs={"data-product-id": True})
        data_product_id = None
        if data_product_div:
            data_product_id = data_product_div["data-product-id"]
        print("city:", city)
        print("product_id:", data_product_id)
        api_url = f"https://www.bethowen.ru/api/local/v1/catalog/products/{data_product_id}/details"

        async with session.get(url=api_url, headers=headers) as response2:
            response_json = await response2.json()
            # print("---")
            # print("json:")
            # print(response_json)
            # print("---")
            # ids = [el["id"] for el in response_json.get("offers")]
            # print("ids:", ids)
            # offers = response_json["offers"]
            # print(f"offers: {offers}")
            name = response_json['name']
            print("name:", name)
            for good in response_json["offers"]:
                print("good_id:", good["id"])
                size = good["size"]
                article = good["code"]
                old_price = good["retail_price"]
                discount_price = good["discount_price"]
                print("size:", size)
                print("article:", article)
                print("old_price:", old_price)
                print("discount_price:", discount_price)
                print('--------')
                result = [city, article, name, size, old_price, discount_price]

"""Информация должна содержать: город, код и наименование товара, цены 
(регулярные и акционные, в отдельных столбцах) и информацию о наличии по каждому из 
вариантов товара (например фасовка: 2.5кг или 12кг) в той ТТ (торговой точке / магазине), 
которая будет задана в файле конфигурации.
"""


async def gather_data():
    # url = ("https://www.bethowen.ru/catalogue/dogs/korma/syxoi/korm-dlya-sobak-more-dlya-srednikh-i-krupnykh-porod-s-yagnenkom-sukh/?oid"
    #      "=578206")
    url = ("https://www.bethowen.ru/catalogue/dogs/korma/lechebnye-korma/korm-dlya-sobak-pro-plan-veterinary-diets-pri-ozhirenii-ptitsa/?oid=253470")

    async with aiohttp.ClientSession() as session:
        response = await session.get(url=url, headers=headers)
        soup = BeautifulSoup(await response.text(), 'lxml')

        tasks = []
        task = asyncio.create_task(get_page(session, url))
        tasks.append(task)

        await asyncio.gather(*tasks)


def retry_with_backoff(max_retries=5, backoff_factor=1):
    """
    Декоратор для выполнения повторных попыток с экспоненциальной задержкой.

    :param max_retries: Максимальное количество попыток
    :param backoff_factor: Множитель задержки
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    # Попробовать выполнить функцию
                    result = func(*args, **kwargs)
                    # print(f"Attempt {attempt + 1}: Success")
                    return result
                except Exception as e:
                    # Если попытка неудачна, вычисляем задержку
                    sleep_time = backoff_factor * (2 ** attempt)
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
            # Если все попытки исчерпаны
            print("All attempts failed.")
            return None
        return wrapper
    return decorator


@retry_with_backoff(max_retries=5, backoff_factor=1)
async def parse_categories(site):
    async with aiohttp.ClientSession() as session:
        categories = {}
        response = await session.get(url=site, headers=headers)
        soup = BeautifulSoup(await response.text(), 'html.parser')
        menu = soup.find("ul", class_="ixi-nav__sub-menu")
        # print(menu)
        if menu:
            # categories = menu.find_all("li", class_=re.compile(r"ixi-nav__second"))
            # print("categories:", categories)
            for level_two in menu.find_all("li", class_=re.compile(r"ixi-nav__second")):
                category = level_two.find("span").text
                categories[category] = []
                print("HEADER =", category)
                for level_three in level_two("li", class_=re.compile(r"ixi-nav__third")):
                    subcategory = level_three.find("a").text
                    url = BETHOWEN + level_three.find("a").get('href')
                    print("sub_category:", subcategory, url)
                    categories[category].append({subcategory: url})
                print("-----------------------")
        # print(categories)
        return categories


# Основная функция для запуска парсинга
async def main():
    # Запуск асинхронного парсинга
    # parse_cat = asyncio.create_task(parse_categories(CATALOGUE_URL))
    categories = await parse_categories(CATALOGUE_URL)
    print(categories)
    # await asyncio.gather(parse_cat)
    # asyncio.run()
    finish_time = time.time() - start_time
    print(f"Затраченное на работу скрипта время: {finish_time}")

