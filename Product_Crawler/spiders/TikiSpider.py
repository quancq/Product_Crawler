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


class TikiSpider(ProductSpider):
    name = "Tiki"
    allowed_domains = ["tiki.vn"]
    base_url = "https://tiki.vn"

    url_category_list = [
        # ("https://tiki.vn/thoi-trang-so-sinh/c5188", "Thời trang sơ sinh"),
        # ("https://tiki.vn/thoi-trang-me-bau/c5191", "Thời trang mẹ bầu"),
        # ("https://tiki.vn/phu-kien-cho-be/c5192", "Phụ kiện cho bé"),
        # ("https://tiki.vn/thoi-trang-be-gai/c5189", "Thời trang bé gái"),
        # ("https://tiki.vn/thoi-trang-be-trai/c5190", "Thời trang bé trai"),
        # ("https://tiki.vn/dinh-duong-cho-be/c8339", "Dinh dưỡng cho bé"),
        # ("https://tiki.vn/dinh-duong-cho-me/c10416", "Dinh dưỡng cho mẹ"),
        # ("https://tiki.vn/ta-bim-cho-be/c2551", "Tã, Bỉm"),
        # ("https://tiki.vn/do-choi/c5250", "Đồ chơi"),
        # ("https://tiki.vn/the-thao-da-ngoai/c1975", "Thể thao"),
        # ("https://tiki.vn/xe-may/c8597", "Xe máy"),
        # ("https://tiki.vn/xe-dien/c6070", "Xe điện"),
        # ("https://tiki.vn/xe-dap/c8431", "Xe đạp"),
        # ("https://tiki.vn/mu-bao-hiem/c11906", "Mũ bảo hiểm"),
        # ("https://tiki.vn/phu-kien-phu-tung-xe-may/c6061", "Phụ kiện, Phụ tùng xe máy"),
        # ("https://tiki.vn/phu-kien-do-nghe-xe-dap/c11904", "Phụ kiện, Phụ tùng xe đạp"),
        # ("https://tiki.vn/phu-kien-o-to/c6045", "Phụ kiện, Phụ tùng ô tô"),
        # ("", ""),
        # ("https://tiki.vn/thiet-bi-cham-soc-suc-khoe/c2307", "Thiết bị chăm sóc sức khỏe"),
        # ("https://tiki.vn/chan-men-va-phu-kien/c23352", "Chăn, mền và phụ kiện"),
        # ("https://tiki.vn/dem-ngoi/c23374", "Đệm ngồi"),
        # ("https://tiki.vn/nem-va-phu-kien/c6723", "Nệm và phụ kiện"),
        # ("https://tiki.vn/thuc-pham-chuc-nang/c2322", "Thực phẩm chức năng"),
        # ("https://tiki.vn/ngoai-troi-san-vuon/c2223", "Ngoài trời, sân vườn"),
        # ("https://tiki.vn/bo-ga-ra-drap/c23346", "Bộ ga, ra, drap"),
        # ("https://tiki.vn/ruot-goi-ruot-chan/c6724", "Gối, ruột gối, vỏ gối"),
        # ("", ""),
        ("https://tiki.vn/noi-that/c2150", "Nội thất"),
        # ("", ""),
    ]
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 '
    #                          '(KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36',
    #            'Origin': 'https://tiki.vn'}
    headers = {'Origin': 'https://tiki.vn'}

    def __init__(self):
        super().__init__(name=self.name)

    def start_requests(self):
        page_idx = 100
        for category_url, category in self.url_category_list:
            meta = {
                "category": category,
                "category_url_fmt": category_url + "?page={}",
                "page_idx": page_idx
            }
            category_url = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(category_url, self.parse_category, meta=meta,
                          errback=self.errback, headers=self.headers)

    def parse_category(self, response):
        meta = dict(response.meta)
        item_urls = response.css(".product-box-list>div>a::attr(href)").extract()

        self.logger.info("Parse url {}, Num item urls : {}".format(response.url, len(item_urls)))
        for item_url in item_urls:
            if utils.is_valid_url(item_url):
                yield Request(item_url, self.parse_item, meta=meta,
                              errback=self.errback, headers=self.headers)

        # Navigate to next page
        if meta["page_idx"] < self.page_per_category_limit and len(item_urls) > 0:
            meta["page_idx"] += 1
            next_page = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(next_page, self.parse_category, meta=meta,
                          errback=self.errback, headers=self.headers)

    def parse_item(self, response):
        # meta = response.meta
        product_id = response.css(".item-box #product_id::attr(value)").extract_first().strip()
        product_name = response.css(".item-box #product-name::text").extract_first().strip()

        try:
            price = response.css(".item-box #span-price::text").extract_first()\
                .strip().replace(u'\xa0', u' ')
        except:
            price = ""

        brand = response.css(".item-box div[itemprop=brand] "
                             "meta[itemprop=name]::attr(content)").extract_first()

        seller = response.css(".item-box .current-seller .name .text span::text").extract_first()

        info = " ".join(response.css(".product-content-detail #gioi-thieu ::text").extract())
        info = re.sub("\s+", " ", info).replace("\xa0", " ")

        item = dict(product_id=product_id, model=product_name, price=price,
                    brand=brand, seller=seller, info=info, category=response.meta["category"],
                    url=response.url)

        review_count = response.css(".item-price .item-rating .-reviews-count::text").extract_first()
        try:
            review_count = int(review_count)
        except:
            review_count = 100

        review_url = "https://tiki.vn/api/v2/reviews?product_id={}&limit={}"\
            .format(product_id, review_count)

        yield Request(review_url, self.parse_reviews, meta=item,
                      errback=self.errback, headers=self.headers)

    def parse_reviews(self, response):
        review_data = json.loads(response.text)

        rating_data = review_data.get("stars", {})
        ratings = {}
        for i in range(1, 6):
            try:
                count = int(rating_data[str(i)]["count"])
            except:
                count = 0
            ratings.update({i: count})

        full_reviews = review_data["data"]
        reviews = []
        for review in full_reviews:
            title = review.get("title", "")
            content = review.get("content", "")
            comment = title + ". " + content
            rating = review.get("rating", "")
            review_time = review.get("created_at")
            review_time = utils.convert_unix_time(review_time)

            try:
                bought_time = review["created_by"]["purchased_at"]
                bought_time = utils.convert_unix_time(bought_time)
            except:
                bought_time = ""

            reviews.append(dict(rating=rating, comment=comment,
                                review_time=review_time, bought_time=bought_time))

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
            price=meta["price"],
            seller=meta["seller"],
            reviews=reviews,
            ratings=ratings,
        )

    def errback(self, failure):
        self.logger.error("Error when send requests : ", failure.request)
