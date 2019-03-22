from scrapy import Request
from Product_Crawler.spiders.ProductSpider import ProductSpider
from Product_Crawler.Crawl import crawl_sendo
from Product_Crawler.items import Product
from Product_Crawler import utils
from Product_Crawler.project_settings import DEFAULT_TIME_FORMAT
from lxml import html
import re
import json
import random


class SendoSpider(ProductSpider):
    name = "Sendo"
    allowed_domains = ["sendo.vn"]
    base_url = "https://www.sendo.vn"

    url_category_list = [
        # ("https://www.sendo.vn/sua-va-thuc-pham-tu-sua/", "Sữa và thực phẩm từ sữa"),
        # ("https://www.sendo.vn/do-uong/", "Đồ uống"),
        # ("https://www.sendo.vn/sua-bot/", "Sữa bột"),
        # ("https://www.sendo.vn/sua-va-thuc-pham-tu-sua-khac/", "Sữa và thực phẩm từ sữa khác"),
        # ("https://www.sendo.vn/sua-cho-nguoi-an-kieng/", "Sữa cho người ăn kiêng"),
        # ("https://www.sendo.vn/vang-sua/", "Váng sữa"),
        # ("https://www.sendo.vn/pho-mai/", "Phô mai"),
        # ("https://www.sendo.vn/sua-chua/", "Sữa chua"),
        # ("https://www.sendo.vn/bo/", "Bơ"),
        # ("https://www.sendo.vn/keo/", "Kẹo"),
        # ("https://www.sendo.vn/mi-pho-chao-an-lien/", "Mì phở cháo ăn liền"),
        # ("https://www.sendo.vn/rau-cu-qua-say-kho/", "Rau củ quả sấy khô"),
        # ("https://www.sendo.vn/ngu-coc-bot/", "Ngũ cốc"),
        # ("https://www.sendo.vn/banh-mut", "Bánh mứt"),
        # ("https://www.sendo.vn/van-phong-pham/", ""),
        # ("https://www.sendo.vn/thiet-bi-di-dong/", "Điện thoại di động"),
        # ("", ""),
        # ("", ""),
        # ("https://www.sendo.vn/trang-suc-thoi-trang/", "Trang sức"),
        # ("https://www.sendo.vn/dong-ho-phu-kien/", "Đồng hồ"),
        # ("https://www.sendo.vn/tui-xach-nu/", "Túi xách nữ"),
        # ("https://www.sendo.vn/tui-xach-nam/", "Túi xách nam"),
        # ("https://www.sendo.vn/balo/", "Balo"),
        # ("https://www.sendo.vn/vali-tui-xach-du-lich/", "Vali - Túi xách du lịch"),
        # ("https://www.sendo.vn/vi-bop-nu/", "Ví nữ"),
        # ("https://www.sendo.vn/vi-bop-nam/", "Ví nam"),
        # ("https://www.sendo.vn/phu-kien-thoi-trang/", "Phụ kiện thời trang"),
        # ("", ""),
        # ("https://www.sendo.vn/thoi-trang-nu/", "Thời trang nữ"),
        # ("https://www.sendo.vn/thoi-trang-nam/", "Thời trang nam"),
        # ("", ""),
        ("https://www.sendo.vn/giay-dep-cao-got-nu/", "Giày dép nữ"),
        ("https://www.sendo.vn/giay-sandals-nu/", "Giày dép nữ"),
        ("https://www.sendo.vn/giay-bot-nu/", "Giày dép nữ"),
        ("https://www.sendo.vn/giay-sneaker-the-thao-nu/", "Giày dép nữ"),
        ("https://www.sendo.vn/dep-nu/", "Giày dép nữ"),
        ("https://www.sendo.vn/giay-luoi-giay-moi-slip-on-nu/", "Giày dép nữ"),
        ("https://www.sendo.vn/giay-nu/", "Giày dép nữ"),
        ("https://www.sendo.vn/giay-dep-nu-big-size/", "Giày dép nữ"),
        # ("", ""),
        # ("https://www.sendo.vn/giay-nam/", "Giày dép nam"),
        # ("https://www.sendo.vn/giay-tay-nam/", "Giày dép nam"),
        # ("https://www.sendo.vn/dep-nam/", "Giày dép nam"),
        # ("https://www.sendo.vn/giay-sneaker-the-thao-nam/", "Giày dép nam"),
        # ("https://www.sendo.vn/giay-moi-giay-luoi-nam/", "Giày dép nam"),
        # ("https://www.sendo.vn/giay-tang-chieu-cao-nam/", "Giày dép nam"),
        # ("https://www.sendo.vn/giay-dep-nam-big-size/", "Giày dép nam"),
        # ("", ""),
        # ("", ""),
    ]

    def __init__(self):
        super().__init__(name=self.name)
    #     catgory_path = "./Product_Crawler/Crawl/Data/Sendo/sendo_category.csv"
    #     self.map_url_category = crawl_sendo.load_category_map(catgory_path, key="Category url")
    #     self.map_id_category = crawl_sendo.load_category_map(catgory_path, key="Category id")

    def start_requests(self):
        page_idx = 1
        for category_url, category in self.url_category_list:
            category_id = self.get_category_id(category_url)
            meta = {
                "category": category,
                "category_id": category_id,
                "category_url_fmt": "https://www.sendo.vn/m/wap_v2/category/product?"
                                    "category_id={}&p={}&s=100&sortType=default_listing_desc",
                "page_idx": page_idx
            }
            category_url = meta["category_url_fmt"].format(meta["category_id"], meta["page_idx"])
            yield Request(category_url, self.parse_category, meta=meta, errback=self.errback)

    def parse_category_from_id(self, category_id, num_items):
        # Get all item
        print("\nCategory id : {}, Number items : {}".format(category_id, num_items))
        item_urls_fmt = "https://www.sendo.vn/m/wap_v2/category/product?" \
                        "category_id={}&p=1&s={}&sortType=default_listing_desc"
        all_item_url = item_urls_fmt.format(category_id, num_items)
        try:
            json_data = json.loads(self.get_response(all_item_url).content.decode("utf-8"))
            full_items = json_data["result"]["data"]
        except:
            self.logger.error("\nError when all items of cat_id : {}, total_items : {}"
                              .format(category_id, num_items))
            return 0

        for full_item in full_items[:7]:

            cat_path = full_item["cat_path"]
            item_url_key = cat_path.replace(".html/", "")
            item_url = "https://www.sendo.vn/m/wap_v2/full/san-pham/{}".format(item_url_key)

            url = self.base_url + "/" + cat_path
            category = self.map_id_category.get(category_id, {}).get("Category name", "")
            item = dict(category=category, category_id=category_id, url=url,
                        product_id=full_item["product_id"], model=full_item["name"],
                        price=full_item["final_price"], seller=full_item["shop_name"])
            if utils.is_valid_url(item_url):
                yield Request(item_url, self.parse_item, meta=item, errback=self.errback)

    def get_category_id(self, category_url):
        # Get category id
        response = self.get_response(category_url)
        root = html.document_fromstring(response.content.decode("utf-8"))
        scripts = root.cssselect("script")
        pre = "window.__INITIAL_STATE__="
        post = "</script>"
        str_data = None
        for script in scripts:
            text = script.text_content()
            if pre in text:
                str_data = text
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
            self.logger.error("\nError when parse json data to get category id of ", category_url)
            return 0

        return category_id

    def parse_category(self, response):
        meta = dict(response.meta)

        # # Get category id
        # scripts = response.css("script").extract()
        # pre = "window.__INITIAL_STATE__="
        # post = "</script>"
        # str_data = None
        # for script in scripts:
        #     if pre in script:
        #         str_data = script
        #         break
        #
        # if str_data is None:
        #     return 0
        #
        # start_index = str_data.find(pre) + len(pre)
        # end_index = str_data.find(post, start_index)
        # str_data = str_data[start_index: end_index]
        #
        # try:
        #     json_data = json.loads(str_data)
        #     category_id = json_data["data"]["ListingInfo"]["active"]["data"]["categoryId"]
        #
        # except:
        #     self.logger.error("\nError when parse json data to get category id of ", meta["category"])
        #     return 0

        # Get total items of category
        # item_urls_fmt = "https://www.sendo.vn/m/wap_v2/category/product?" \
        #                 "category_id={}&p={}&s={}&sortType=default_listing_desc"
        # page_id = random.randint(1, 6)
        # url = item_urls_fmt.format(category_id, page_id, 5)
        # try:
        #     json_data = json.loads(self.get_response(url).content.decode("utf-8"))
        #     total_items = json_data["result"]["meta_data"]["total_count"]
        # except:
        #     self.logger.error("\nError when get number items of "
        #                       "category {}, cat_id : {}".format(meta["category"], category_id))
        #     return 0

        # Get all item
        # total_items = 500
        # all_item_url = item_urls_fmt.format(category_id, 1, total_items)
        try:
            # json_data = json.loads(self.get_response(all_item_url).content.decode("utf-8"))
            json_data = json.loads(response.text)
            full_items = json_data["result"]["data"]
        except:
            self.logger.error("\nError when all items of category {}, cat_id : {}"
                              .format(meta["category"], meta["category_id"]))
            return 0

        self.logger.info("Parse url {}, Num item urls : {}".format(response.url, len(full_items)))
        for full_item in full_items:

            cat_path = full_item["cat_path"]
            item_url_key = cat_path.replace(".html/", "")
            item_url = "https://www.sendo.vn/m/wap_v2/full/san-pham/{}".format(item_url_key)

            url = self.base_url + "/" + cat_path
            item = dict(category=meta["category"], category_id=meta["category_id"], url=url,
                        product_id=full_item["product_id"], model=full_item["name"],
                        price=full_item["final_price"], seller=full_item["shop_name"])

            if utils.is_valid_url(item_url):
                yield Request(item_url, self.parse_item, meta=item, errback=self.errback)

        # Navigate to next page
        if meta["page_idx"] < self.page_per_category_limit and len(full_items) > 0:
            meta["page_idx"] += 1
            next_page = meta["category_url_fmt"].format(meta["category_id"], meta["page_idx"])
            yield Request(next_page, self.parse_category, meta=meta, errback=self.errback)

    def parse_item(self, response):
        meta = response.meta
        product_id = meta["product_id"]

        json_data = json.loads(response.text)
        items_data = json_data["result"]["data"]

        try:
            description = items_data["description"]
            root = html.document_fromstring(description)

            info = root.text_content()
            info = re.sub("\s+", " ", info)
        except:
            info = ""

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

        try:
            ratings = {r: items_data["rating_info"].get("star{}".format(r), 0) for r in range(1, 6)}
        except:
            ratings = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        # Add new scraped data
        meta.update({
            "info": info,
            "brand": brand,
            "others": others,
            "ratings": ratings,
            "tags": tags
        })

        # Crawl reviews of product
        num_ratings = items_data["rating_info"].get("total_rated", 0)
        review_url = "https://www.sendo.vn/m/wap_v2/san-pham/rating/{}?p=1&s={}".format(product_id, num_ratings)
        yield Request(review_url, self.parse_reviews, meta=meta, errback=self.errback)

    def parse_reviews(self, response):
        review_data = json.loads(response.text)
        full_reviews = review_data["result"]["data"]

        reviews = []
        for full_review in full_reviews:
            rating = full_review["star"]
            comment = full_review["content"]
            review_time = full_review["update_time"]
            review_time = utils.transform_time_fmt(review_time, src_fmt="%H:%M, %d thg %m, %Y",
                                                   dst_fmt=DEFAULT_TIME_FORMAT)

            reviews.append(dict(rating=rating, comment=comment, review_time=review_time))

        self.item_scraped_count += 1
        self.print_num_scraped_items(every=20)

        meta = response.meta
        yield Product(
            domain=self.allowed_domains[0],
            product_id=meta["product_id"],
            url=meta["url"],
            brand=meta["brand"],
            category=meta["category"],
            model=meta["model"],
            info=meta["info"],
            tags=meta["tags"],
            price=meta["price"],
            seller=meta["seller"],
            reviews=reviews,
            ratings=meta["ratings"],
            others=meta["others"]
        )

    def errback(self, failure):
        self.logger.error("Error when send requests : ", failure.request)
