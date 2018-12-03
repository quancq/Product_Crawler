import requests
from lxml import html
from Product_Crawler import utils
import pandas as pd
import json


def crawl_item_urls(page_url=None):
    if page_url is None:
        page_url = "https://www.lazada.vn/ca-phe/?ajax=false&page=1"

    content = requests.get(page_url).content.decode("utf-8")
    print("Page url : ", page_url)
    print(content)
    data = json.loads(content)
    items = data["mods"]["listItems"]
    item_urls, item_ids = [], []
    for item in items:
        item_urls.append(item["productUrl"])
        item_ids.append(item["itemId"])

    page_id = page_url[page_url.rfind("page=") + 5:]
    utils.save_list(item_ids, "./Data/Lazada/itemId_page{}.txt".format(page_id))
    return item_urls


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

