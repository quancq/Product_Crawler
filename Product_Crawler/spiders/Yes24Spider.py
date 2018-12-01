import scrapy
from scrapy import Request
from Product_Crawler.spiders.ProductSpider import ProductSpider
from Product_Crawler.items import Product
from Product_Crawler import utils


class Yes24Spider(ProductSpider):
    name = "Yes24"
    allowed_domains = ["yes24.vn"]
    base_url = "https://www.yes24.vn"

    url_category_list = [
        ("https://www.yes24.vn/thuc-pham/thuc-pham-chuc-nang-c679630", "Thực phẩm chức năng"),
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
        intro_div = response.css("#tr-intro-productdt")
        model = intro_div.css(".tr-prd-name2::text").extract_first().strip()
        brand = intro_div.css(".tr-thuonghieu-reg>a::text").extract_first().strip()
        category = response.meta["category"]

        # intro = intro_div.css(".tr-short-content::text").extract()
        # intro = [elm.strip() for elm in intro]
        # intro = " ".join(intro)

        price = intro_div.css(".th-detail-price::text").extract_first().strip()
        info = response.css("#tr-detail-productdt .tr-prd-info-content ::text").extract()
        text = " ".join([elm.strip() for elm in info])

        self.item_scraped_count += 1
        if self.item_scraped_count % 100 == 0:
            self.logger.info("Spider {}: Crawl {} items".format(self.name, self.item_scraped_count))

        yield Product(
            url=url,
            brand=brand,
            category=category,
            model=model,
            text=text,
            price=price
        )

    def errback(self, failure):
        self.logger.error("Error when send requests : ", failure.request)
