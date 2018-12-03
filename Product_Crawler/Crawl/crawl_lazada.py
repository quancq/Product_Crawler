import requests
from lxml import html
from Product_Crawler import utils
import pandas as pd
import json


def crawl_item_urls(page_url=None):
    if page_url is None:
        page_url = "https://www.lazada.vn/ca-phe/?ajax=false&page=1"

    content = requests.get(page_url).content.decode("utf-8")
    data = json.loads(content)
    items = data["mods"]["listItems"]
    # utils.save_json(items, "./Data/Lazada/temp1")
    item_urls = []
    for item in items:
        item_urls.append(item["productUrl"])

    return content


if __name__ == "__main__":
    # crawl_item_urls()
    # page_url_fmt = "https://www.lazada.vn/ca-phe/?ajax=false&page={}"
    # item_urls = []
    # for page in range(1, 2):
    #     page_url = page_url_fmt.format(page)
    #     item_urls_of_page = crawl_item_urls(page_url)
    #     item_urls.extend(item_urls_of_page)
    #
    # print("All item urls : ", len(item_urls))
    # unique_item_urls = list(set(item_urls))
    # print("Unique item urls : ", len(unique_item_urls))
    #
    # save_path = "./Data/Lazada/temp"
    # utils.save_list(unique_item_urls, save_path)

    page_url_fmt = "https://www.lazada.vn/ca-phe/?ajax=false&page={}"
    c1 = crawl_item_urls(page_url_fmt.format(1))
    c2 = crawl_item_urls(page_url_fmt.format(2))

    c1 = json.loads(c1)
    c2 = json.loads(c2)

    utils.save_json(c1, "./Data/Lazada/c1.txt")
    utils.save_json(c2, "./Data/Lazada/c2.txt")
