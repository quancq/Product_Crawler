from lxml import html
from xml.etree import ElementTree as ET
from Product_Crawler import utils
import pandas as pd
import json
import time
import random
from Product_Crawler.crawl_proxy import ProxyManager


class SendoCrawler:
    def __init__(self):
        self.pm = ProxyManager(proxies_path="../Proxy/proxy_list.txt", update=True)

    def crawl_category_id(self, category_url="https://www.sendo.vn/cong-nghe/thiet-bi-di-dong/"):
        root = html.document_fromstring(self.pm.get_response(category_url).content)

        # Get category id
        scripts = root.cssselect("script")
        pre = "window.__INITIAL_STATE__="
        post = "</script>"
        str_data = None
        for script in scripts:
            text = script.text_content()
            if pre in text:
                str_data = text
                break

        category_info = {}
        if str_data is not None:
            start_index = str_data.find(pre) + len(pre)
            end_index = str_data.find(post, start_index)
            str_data = str_data[start_index: end_index]

            try:
                json_data = json.loads(str_data)
                json_data = json_data["data"]["ListingInfo"]["active"]["data"]
                category_id = json_data["categoryId"]
                category_name = json_data["title"]
                sub_category_ids = []
                for sub_category in json_data["subCategories"]:
                    sub_category_ids.append(sub_category.get("id", ""))

                parent_category_ids = []
                for parent_category in json_data["categoryInfo"]:
                    parent_category_ids.append(parent_category.get("id", ""))

                # Crawl number items of category
                page_random = random.randint(1, 5)
                items_url = "https://www.sendo.vn/m/wap_v2/category/product?category_id={}&p={}&s=60" \
                            "&sortType=default_listing_desc".format(category_id, page_random)

                try:
                    json_data = json.loads(self.pm.get_response(items_url).content.decode("utf-8"))
                    num_items = json_data["result"]["meta_data"]["total_count"]
                except:
                    num_items = 0

                category_info = dict(category_url=category_url,
                                     category_id=category_id,
                                     category_name=category_name,
                                     parent_category_ids=parent_category_ids,
                                     sub_category_ids=sub_category_ids,
                                     num_items=num_items)

            except:
                return {}
        else:
            return {}

        return category_info

    @staticmethod
    def get_urls(xml_path="./Data/Sendo/category.xml"):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # print(ET.tostring(root))

        urls = list(root.findall("url/loc"))
        urls = [url_elm.text for url_elm in urls]
        return urls

    def build_category_relationship(self, xml_path="./Data/Sendo/category.xml"):
        start_time = time.time()

        urls = self.get_urls(xml_path)
        print(len(urls))
        # urls = urls[1200:]

        columns = ["Category url", "Category id", "Category name",
                   "Number items", "Parent category id", "Sub category id"]
        categories = []
        save_path = "./Data/Sendo/sendo_category.csv"
        for i, cat_url in enumerate(urls):
            cat_info = self.crawl_category_id(cat_url)

            if len(cat_info) > 0:
                cat_url, cat_id = cat_info["category_url"], cat_info["category_id"]
                cat_name, num_items = cat_info["category_name"], cat_info["num_items"]
                parent_ids, sub_ids = cat_info["parent_category_ids"], cat_info["sub_category_ids"]

                parent_ids = "-".join([str(id) for id in parent_ids])
                sub_ids = "-".join([str(id) for id in sub_ids])

                categories.append((cat_url, cat_id, cat_name, num_items,
                                    parent_ids, sub_ids))

                print("Crawl {}/{} done. Category url : {}, ID : {}, "
                      "Name : {}, Number items : {}, ParentID : {}, SubID : {}".format(
                        i+1, len(urls), cat_url, cat_id, cat_name, num_items, parent_ids, sub_ids))

            # if (i+1) % 5 == 0:
            #     save_df = pd.DataFrame(categories, columns=columns)
            #     utils.save_csv(save_df, save_path)
            #
            # if (i+1) % 4 == 0:
            #     print("Slepping ...")
            #     time_sleep = random.randint(1, 5)
            #     time.sleep(time_sleep)
            #
            # i_random = random.randint(1, 4)
            # if (i+1) % i_random == 0:
            #     print("Slepping ...")
            #     time_sleep = random.randint(1, 4)
            #     time.sleep(time_sleep)

        exec_time = time.time() - start_time
        print("Build file {} done. Time : {:.2f} seconds".format(save_path, exec_time))

    def get_correct_urls(self):
        start_time = time.time()
        path = "./Data/Sendo/sendo_category.csv"
        df = utils.load_csv(path)
        df = df[:5]

        category_urls = df["Category url"].values.tolist()
        correct_category_urls = []
        num_diff_urls = 0
        for i, url in enumerate(category_urls):
            res = self.pm.get_response(url)
            if res is not None:
                correct_category_urls.append(res.url)
                if res.url != url:
                    num_diff_urls += 1
                    # print("Old: {} - New: {}".format(url, res.url))
            else:
                correct_category_urls.append(url)
            if (i+1) % 5 == 0:
                print("{}/{} get correct category urls done".format(i+1, len(category_urls)))

        print("Number different urls : ", num_diff_urls)
        df["Category url"] = correct_category_urls
        utils.save_csv(df, "./Data/Sendo/sendo_category_new_url.csv")

        exec_time = time.time() - start_time
        print("Correct category urls done. Time : {:.2f} seconds".format(exec_time))


def load_category_map(category_path="./Data/Sendo/sendo_category.csv", key="Category url"):
    df = utils.load_csv(category_path)
    if key not in df.columns:
        key = "Category url"

    df.set_index(key, inplace=True)
    map = df.to_dict("index")

    return map


def test():
    sc = SendoCrawler()
    sc.get_correct_urls()


if __name__ == "__main__":
    pass
    # sc = SendoCrawler()
    test()

