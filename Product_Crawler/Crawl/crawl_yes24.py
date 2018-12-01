import requests
from lxml import html
from Product_Crawler import utils
import pandas as pd
import time


def get_brands():
    start_time = time.time()
    url = "https://www.yes24.vn/"
    root = html.document_fromstring(requests.get(url).content)

    # Find category and url
    category_urls = []

    li_elms = root.cssselect("#menu-bottom ul.tr-list-menu>li")
    for li in li_elms:
        parent_cat = li.cssselect("h2>a")[0].text

        sub_a_elms = li.cssselect("ul.tr-list-ds-con>li>a")
        for a in sub_a_elms:
            child_cat = a.text
            cat = parent_cat + " - " + child_cat
            url = a.attrib["href"]

            category_urls.append((cat, url))

    # for cat, url in category_urls[:4]:
    #     print("Category : {} - Url : {}".format(cat, url))
    #
    # print("Number category : ", len(category_urls))

    map_cat_brands = {}
    # Crawl brands of each category
    # category_urls = category_urls[:4]
    for i, (cat, url) in enumerate(category_urls):
        root = html.document_fromstring(requests.get(url).content)

        # Find brandSearchUrl in script tag to send request and receive brands
        brand_search_url = None
        scripts = root.cssselect("script")
        for script in scripts:
            text = script.text_content()
            index = text.find("brandSearchUrl")
            if index >= 0:
                start_index = text.find("'", index)
                end_index = text.find("'", start_index+1)
                brand_search_url = text[start_index+1: end_index]
                break
        if brand_search_url is not None:
            # Crawl brands
            brand_search_url = "https://www.yes24.vn" + brand_search_url.replace("&amp;", "&")
            root = html.document_fromstring(requests.get(brand_search_url).content)

            a_elms = root.cssselect("ul.th-brand-list>li>a")
            brands = [a.attrib["data-val"] for a in a_elms]

            map_cat_brands.update({cat: brands})
            print("Crawl brands of {}/{} categories done".format(i+1, len(category_urls)))

    # for cat, brands in map_cat_brands.items():
    #     print("Category : {}, Brands : {}".format(cat, brands))

    cat_brands = []
    for cat, brands in map_cat_brands.items():
        cat_brands.append((cat, ','.join(brands)))

    save_path = "./Data/Yes24/Category_Brands.json"
    utils.save_json(map_cat_brands, save_path)

    df = pd.DataFrame(cat_brands, columns=["Category", "Brands"])
    save_path = "./Data/Yes24/Category_Brands.csv"
    utils.save_csv(df, save_path)

    exec_time = time.time() - start_time
    print("Crawl brands of {} categories done. Time : {:.2f} seconds".format(
        len(map_cat_brands), exec_time))

    return map_cat_brands


if __name__ == "__main__":
    get_brands()
