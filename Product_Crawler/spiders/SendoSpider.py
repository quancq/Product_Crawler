import scrapy
from scrapy import Request
from Product_Crawler.spiders.ProductSpider import ProductSpider
from Product_Crawler.items import Product
from Product_Crawler import utils
from Product_Crawler.project_settings import DEFAULT_TIME_FORMAT
from lxml import html
import requests
import math
import re
import json


class SendoSpider(ProductSpider):
    name = "Sendo"
    allowed_domains = ["sendo.vn"]
    base_url = "https://www.sendo.vn"

    url_category_list = [
        ("https://www.sendo.vn/sua-va-thuc-pham-tu-sua/", "Sữa và thực phẩm từ sữa")
    ]

    def start_requests(self):
        page_idx = 1
        for category_url, category in self.url_category_list:
            meta = {
                "category": category,
                "category_url_fmt": category_url + "?p={}",
                "page_idx": page_idx
            }
            category_url = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(category_url, self.parse_category, meta=meta, errback=self.errback)

    def parse_category(self, response):
        meta = dict(response.meta)

        # Get category id
        scripts = response.css("script").extract()
        pre = "window.__INITIAL_STATE__="
        post = "</script>"
        str_data = None
        for script in scripts:
            if pre in script:
                str_data = script
                break

        if str_data is None:
            return 0

        start_index = str_data.find(pre) + len(pre)
        end_index = str_data.find(post, start_index)
        str_data = str_data[start_index: end_index]

        try:
            json_data = json.loads(str_data)
            category_id = json_data["data"]["ListingInfo"]["active"]["data"]["categoryId"]

        except:
            self.logger.error("\nError when parse json data to get category id of ", meta["category"])
            return 0

        # Get total items of category
        item_urls_fmt = "https://www.sendo.vn/m/wap_v2/category/product?" \
                        "category_id={}&p=1&s={}&sortType=default_listing_desc"
        url = item_urls_fmt.format(category_id, 1)
        try:
            json_data = json.loads(requests.get(url).content.decode("utf-8"))
            total_items = json_data["result"]["meta_data"]["total_count"]
        except:
            self.logger.error("\nError when get number items of "
                              "category {}, cat_id : {}".format(meta["category"], category_id))
            return 0

        # Get all item
        all_item_url = item_urls_fmt.format(category_id, total_items)
        try:
            json_data = json.loads(requests.get(all_item_url).content.decode("utf-8"))
            full_items = json_data["result"]["data"]
        except:
            self.logger.error("\nError when all items of category {}, cat_id : {}, total_items : {}"
                              .format(meta["category"], category_id, total_items))
            return 0

        self.logger.info("Parse url {}, Num item urls : {}".format(response.url, len(full_items)))
        for full_item in full_items[:6]:

            cat_path = full_item["cat_path"]
            item_url_key = cat_path.replace(".html/", "")
            item_url = "https://www.sendo.vn/m/wap_v2/full/san-pham/{}".format(item_url_key)

            url = self.base_url + "/" + cat_path
            item = dict(category=meta["category"], category_id=category_id, url=url,
                        product_id=full_item["product_id"], model=full_item["name"],
                        price=full_item["final_price"], seller=full_item["shop_name"])

            if utils.is_valid_url(item_url):
                yield Request(item_url, self.parse_item, meta=item, errback=self.errback)

    def parse_item(self, response):
        meta = response.meta
        url = meta["url"]
        category = meta["category"]
        product_id = meta["product_id"]
        model = meta["model"]
        seller = meta["seller"]
        price = meta["price"]

        json_data = json.loads(response.text)
        items_data = json_data["result"]["data"]
        description = items_data["description"]
        root = html.document_fromstring(description)

        info = root.text_content()
        info = re.sub("\s+", " ", info)

        try:
            brand = items_data["brand_info"].get("name", "")
        except:
            brand = ""

        full_category_id = items_data["category_id"]
        order_count = items_data["order_count"]
        counter_view = items_data["counter_view"]

        shop_info = items_data["shop_info"]
        shop_info = dict(shop_id=shop_info.get("shop_id", ""),
                         shop_name=shop_info.get("shop_name", ""),
                         good_review_percent=shop_info.get("good_review_percent", ""),
                         warehourse_region_name=shop_info.get("warehourse_region_name", ""),
                         phone_number=shop_info.get("phone_number", ""),
                         shop_url=shop_info.get("shop_url", ""),
                         rating_avg=shop_info.get("rating_avg", ""),
                         rating_count=shop_info.get("rating_count", ""),
                         product_total=shop_info.get("product_total", ""))

        others = dict(full_category_id=full_category_id,
                      order_count=order_count,
                      counter_view=counter_view,
                      shop_info=shop_info)

        tags = json_data.get("keywords", "")

        ratings = {r: items_data["rating_info"].get("star{}".format(r), 0) for r in range(1, 6)}

        # Crawl reviews of product
        num_ratings = items_data["rating_info"].get("total_rated", 0)
        num_ratings = 10
        review_url = "https://www.sendo.vn/m/wap_v2/san-pham/rating/{}?p=1&s={}".format(product_id, num_ratings)

        review_data = json.loads(requests.get(review_url).content.decode("utf-8"))
        full_reviews = review_data["result"]["data"]

        reviews = []
        for full_review in full_reviews:
            rating = full_review["star"]
            comment = full_review["content"]
            review_time = full_review["update_time"]
            review_time = utils.transform_time_fmt(review_time, src_fmt="%H:%M, %d thg %m, %Y", dst_fmt=DEFAULT_TIME_FORMAT)

            reviews.append(dict(rating=rating, comment=comment, review_time=review_time))

        self.item_scraped_count += 1
        if self.item_scraped_count % 100 == 0:
            self.logger.info("Spider {}: Crawl {} items".format(self.name, self.item_scraped_count))

        yield Product(
            domain=self.allowed_domains[0],
            product_id=product_id,
            url=url,
            brand=brand,
            category=category,
            model=model,
            info=info,
            tags=tags,
            price=price,
            seller=seller,
            reviews=reviews,
            ratings=ratings,
            others=others
        )

    def errback(self, failure):
        self.logger.error("Error when send requests : ", failure.request)
