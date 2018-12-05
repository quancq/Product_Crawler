import scrapy
from scrapy import Request
from Product_Crawler.spiders.ProductSpider import ProductSpider
from Product_Crawler.items import Product
from Product_Crawler import utils
from Product_Crawler.project_settings import DEFAULT_TIME_FORMAT
from lxml import html
import requests
import math


class Yes24Spider(ProductSpider):
    name = "Yes24"
    allowed_domains = ["yes24.vn"]
    base_url = "https://www.yes24.vn"

    url_category_list = [
        # ("https://www.yes24.vn/thuc-pham/thuc-pham-chuc-nang-c679630", "Thực phẩm chức năng"),
        # ("https://www.yes24.vn/me-be", "Mẹ và bé"),
        # ("https://www.yes24.vn/gia-dung", "Gia dụng"),
        # ("https://www.yes24.vn/dien-may", "Điện máy"),
        # ("https://www.yes24.vn/phu-kien", "Phụ kiện"),
        ("https://www.yes24.vn/thuc-pham/thuc-pham-chuc-nang-c679630", "Thực phẩm chức năng"),
        # ("", ""),
    ]

    def start_requests(self):
        page_idx = 1
        for category_url, category in self.url_category_list:
            meta = {
                "category": category,
                "category_url_fmt": category_url + "?item=120&page={}",
                "page_idx": page_idx
            }
            category_url = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(category_url, self.parse_category, meta=meta, errback=self.errback)

    def parse_category(self, response):
        meta = dict(response.meta)

        # Navigate to item
        item_urls = response.css(".th-product-item>a::attr(href)").extract()

        self.logger.info("Parse url {}, Num item urls : {}".format(response.url, len(item_urls)))
        for item_url in item_urls:
            # item_url = self.base_url + item_url

            if utils.is_valid_url(item_url):
                yield Request(item_url, self.parse_item, meta={"category": meta["category"]},
                              errback=self.errback)

        # Navigate to next page
        if meta["page_idx"] < self.page_per_category_limit and len(item_urls) > 0:
            meta["page_idx"] += 1
            next_page = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(next_page, self.parse_category, meta=meta, errback=self.errback)

    def parse_item(self, response):
        url = response.url
        category = response.meta["category"]
        intro_div = response.css("#tr-intro-productdt")
        product_id = response.css("#productNo::attr(value)").extract_first()
        model = intro_div.css(".tr-prd-name2::text").extract_first().strip()
        brand = intro_div.css(".tr-thuonghieu-reg>a::text").extract_first().strip()
        seller_url = intro_div.css(".tr-gn-supplier a::attr(href)").extract_first()

        # Crawl seller name
        root = html.document_fromstring(requests.get(seller_url).content)
        name_elms = root.cssselect(".tr-pr-name1")
        if len(name_elms) > 0:
            seller = name_elms[0].text
        else:
            seller = ""

        # intro = intro_div.css(".tr-short-content::text").extract()
        # intro = [elm.strip() for elm in intro]
        # intro = " ".join(intro)

        price = intro_div.css(".th-detail-price::text").extract_first().strip()
        info = response.css("#tr-detail-productdt .tr-prd-info-content ::text").extract()
        info = " ".join([elm.strip() for elm in info])

        # Calculate rating count
        num_reviews = response.css("#tr-productdt-rank .vote-count::text").extract_first()
        num_reviews = 0 if num_reviews is None else int(num_reviews)

        ratings = response.css("#tr-productdt-rank "
                               ".tr-rank-percent>div:nth-child(3)::text").extract()
        ratings = [float(r[:-1]) for r in ratings]
        ratings = {5-i: int(round(num_reviews * r / 100)) for i, r in enumerate(ratings)}

        # Crawl all reviews of product
        num_page_reviews = int(math.ceil(num_reviews / 5))

        reviews = self.crawl_review(url=None, raw_html=response.text)
        for page in range(2, num_page_reviews + 1):
            url = "https://www.yes24.vn/Product/" \
                  "GetProductComment?productNo={}&page={}".format(product_id, page)
            reviews.extend(self.crawl_review(url))

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
    def crawl_review(url, raw_html=None):
        # url = "https://www.yes24.vn/Product/GetProductComment?productNo=1714033&page=17"
        if url is None:
            root = html.document_fromstring(raw_html)
        else:
            res = requests.get(url)
            res.encoding = "latin-1"
            root = html.document_fromstring(res.content)

        # print(html.tostring(root, pretty_print=True))

        review_divs = root.cssselect("div.tr-comment-detail")

        reviews = []
        for review_div in review_divs:
            spans = review_div.cssselect(".tr-cmtdt-star-date>span")
            rating = len(spans[0].cssselect("span.tr-fa-yellow"))

            time = spans[1].text
            # convert time to setting format
            time = utils.transform_time_fmt(
                time,
                src_fmt="%H:%M:%S, %d/%m/%Y",
                dst_fmt=DEFAULT_TIME_FORMAT
            )

            comment = review_div.cssselect(".tr-cmdt-content-bottom")[0].text.strip()
            if url is not None:
                comment = comment.encode("latin-1").decode("utf-8")
            reviews.append(dict(rating=rating, review_time=time,
                                comment=comment, bought_time=""))

        # for review in reviews:
        #     print("Time : {} - Star : {} - Comment : {}".format(
        #         review["review_time"], review["rating"], review["comment"]))
        return reviews
