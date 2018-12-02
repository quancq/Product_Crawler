import scrapy
from scrapy import Request
from Product_Crawler.spiders.ProductSpider import ProductSpider
from Product_Crawler.items import Product
from Product_Crawler import utils
from Product_Crawler.project_settings import DEFAULT_TIME_FORMAT
from lxml import html
import requests
import math
import json
import html as h


class LazadaSpider(ProductSpider):
    name = "Lazada"
    allowed_domains = ["lazada.vn"]
    base_url = "https://www.lazada.vn"

    url_category_list = [
        # ("https://www.lazada.vn/ca-phe/", "Cà phê"),
        # ("https://www.lazada.vn/snack-do-an-vat/", "Snack Đồ ăn vặt"),
        ("https://www.lazada.vn/dien-thoai-di-dong/", "Điện thoại di động")
    ]

    def start_requests(self):
        page_idx = 1
        for category_url, category in self.url_category_list:
            meta = {
                "category": category,
                "category_url_fmt": category_url + "?spm=a2o4n.searchlistcategory.0.0.29315d52C9PFlW&page={}",
                "page_idx": page_idx
            }
            category_url = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(category_url, self.parse_category, meta=meta, errback=self.errback)

    def parse_category(self, response):
        meta = dict(response.meta)

        # Find item data in script tag
        scripts = response.css("script").extract()
        prefix = "<script>window.pageData="
        postfix = "</script>"
        data = "{}"
        for script in scripts:
            if script.startswith(prefix):
                data = script
                break
        data = data[len(prefix):-len(postfix)]
        data = json.loads(data)
        items = data["mods"]["listItems"]

        self.logger.info("Parse url {}, Num item urls : {}".format(response.url, len(items)))
        for item in items:
            # item_url = self.base_url + item_url
            item_url = "https:" + item["productUrl"]
            item_data = dict(product_id=item["itemId"], model=item["name"], price=item["priceShow"],
                             description=item["description"], num_reviews=item["review"],
                             brand=item["brandName"], seller=item["sellerName"])
            # print("\n\n\nItem url : {}\n\n\n".format(item_url))
            if utils.is_valid_url(item_url):
                yield Request(item_url, self.parse_item,
                              meta=dict(category=meta["category"], item=item_data),
                              errback=self.errback)
            else:
                print("\n\nERROR         XXXXXXXx     xXXX\nItem url : {}\n\n\n".format(item_url))

        # Navigate to next page
        print("\n\n\n======== NEXT NEXT NEXT NEXT NEXT =========\n\n")
        print("------  Page:  {} ---- Len(items): {}   --------\n".format(meta["page_idx"]+1, len(items)))
        if meta["page_idx"] < self.page_per_category_limit and len(items) > 0:
            print("\n\n\n======== NEXT NEXT NEXT NEXT NEXT =========\n\n")
            print("------    {}    --------".format(meta["page_idx"] + 1))
            print("\n\n\n======== NEXT NEXT NEXT NEXT NEXT =========\n\n")
            meta["page_idx"] += 1
            next_page = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(next_page, self.parse_category, meta=meta, errback=self.errback)

    def parse_item(self, response):
        item = response.meta["item"]
        url = response.url
        category = response.meta["category"]

        product_id = item.get("product_id", "")
        model = item.get("model", "")
        brand = item.get("brand", "")
        seller = item.get("seller", "")
        price = item.get("price", "")

        description = item.get("description", [""])
        description = description[0]
        num_reviews = item["num_reviews"]       # This is number ratings, not reviews

        # Extract full info of product
        info = ""
        try:
            scripts = response.css("script").extract()
            keyword = "pageUrl"
            page_url = ""
            for script in scripts:
                start_index = script.find(keyword)
                if start_index >= 0:
                    start_index = start_index + len(keyword) + 3
                    end_index = script.find('"', start_index)
                    page_url = "https:" + script[start_index: end_index]
                    break
            if utils.is_valid_url(page_url):
                res_content = requests.get(page_url).content.decode("raw_unicode_escape")
                sub_str = '"moduleData":{"html"'
                start_index = res_content.find(sub_str)
                if start_index >= 0:
                    start_index += len('"moduleData":')
                    end_index = res_content.find("}]}", start_index) + 3
                    json_str = res_content[start_index: end_index]
                    json_str = h.unescape(json_str)
                    try:
                        json_data = json.loads(json_str)
                    except:
                        print("\n\nRes_content\n{}\n\n".format(res_content))
                        print("Start_index : {} --- End_index : {}\n\n".format(start_index, end_index))
                        postfix = '"picture":""}'
                        end_index = res_content.find(postfix, start_index) + len(postfix)
                        print("Start_index : {} --- End_index : {}\n\n".format(start_index, end_index))
                        json_str = res_content[start_index: end_index]
                        json_data = json.loads(json_str)
                        print("\n\n Parse json 2nd successful\n\n")

                    div_str = json_data["html"].strip()
                    div_elm = html.document_fromstring(div_str)
                    info = div_elm.text_content()
                    info = utils.remove_duplicate_whitespaces(info)
                    # print("\n====X=====\n {} \n====X====\n".format(res_content))
        except:
            print("Error when extract info of item ", url)

        info = description + " " + info

        # Crawl ratings and reviews
        review_url = "https://my.lazada.vn/pdp/review/getReviewList?" \
                     "itemId={}&pageSize={}&filter=0&sort=0&pageNo=1".format(product_id, num_reviews)
        ratings, reviews = self.crawl_reviews(review_url)

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
            price=price,
            seller=seller,
            reviews=reviews,
            ratings=ratings
        )

    def errback(self, failure):
        self.logger.error("Error when send requests : ", failure.request)

    @staticmethod
    def crawl_reviews(url):
        # url = "https://my.lazada.vn/pdp/review/getReviewList?
        # itemId=102463766&pageSize=15&filter=0&sort=0&pageNo=1"
        ratings, reviews = {}, []
        if utils.is_valid_url(url):
            json_data = json.loads(requests.get(url).content.decode("utf-8"))
            scores = json_data["model"]["ratings"]["scores"] or []
            ratings = {5-i: rating for i, rating in enumerate(scores)}

            full_reviews = json_data["model"]["items"] or []
            reviews = []
            for full_review in full_reviews:
                rating = full_review["rating"]

                review_time = full_review["zonedReviewTime"]
                review_time = utils.convert_unix_time(review_time)

                bought_time = full_review["zonedBoughtDate"]
                bought_time = utils.convert_unix_time(bought_time)

                review_title = full_review.get("reviewTitle", "") or ""
                review_content = full_review.get("reviewContent", "") or ""
                comment = review_title + " " + review_content

                reviews.append(dict(rating=rating, review_time=review_time,
                                    comment=comment, bought_time=bought_time))

        # for review in reviews:
        #     print("Time : {} - Star : {} - Comment : {}".format(
        #         review["review_time"], review["rating"], review["comment"]))

        return ratings, reviews
