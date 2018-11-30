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
        # ("https://www.yes24.vn/thuc-pham/thuc-pham-chuc-nang-c679630", "Thực phẩm chức năng"),
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

        # Navigate to product
        product_urls = response.css(".th-product-item>a::attr(href)").extract()

        self.logger.info("Parse url {}, Num Product urls : {}".format(response.url, len(product_urls)))
        for product_url in product_urls:
            # product_url = self.base_url + product_url

            if utils.is_valid_url(product_url):
                yield Request(product_url, self.parse_product, meta={"category": meta["category"]},
                              errback=self.errback)

        # Navigate to next page
        if meta["page_idx"] < self.page_per_category_limit and len(product_urls) > 0:
            meta["page_idx"] += 1
            next_page = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(next_page, self.parse_category, meta=meta, errback=self.errback)

    def parse_product(self, response):
        # This method havent coded !!!!!!!!!
        content_div = response.css(".contentleft")

        url = response.url
        lang = self.lang
        title = content_div.css(".titledetail h1::text").extract_first()
        category = response.meta["category"]
        intro = content_div.css("#ContentRightHeight .sapo::text").extract_first()
        content = ' '.join(content_div.css("#ContentRightHeight #divNewsContent ::text").extract())
        time = content_div.css("#ContentRightHeight .ngayxuatban::text").extract_first()

        # Transform time to uniform format
        if time is not None:
            time = time.strip()
            time = self.transform_time_fmt(time, src_fmt="%d/%m/%Y %H:%M")

        self.article_scraped_count += 1
        if self.article_scraped_count % 100 == 0:
            self.logger.info("Spider {}: Crawl {} items".format(self.name, self.article_scraped_count))

        yield Article(
            url=url,
            lang=lang,
            title=title,
            category=category,
            intro=intro,
            content=content,
            time=time
        )

    def errback(self, failure):
        self.logger.error("Error when send requests : ", failure.request)
