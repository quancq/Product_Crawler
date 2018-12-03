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


class MediamartSpider(ProductSpider):
    name = "Mediamart"
    allowed_domains = ["mediamart.vn"]
    base_url = "https://mediamart.vn"

    url_category_list = [
        # ("https://mediamart.vn/may-giat/", "Máy giặt"),
        ("https://mediamart.vn/smartphones/", "Điện thoại di động")
    ]

    def start_requests(self):
        page_idx = 1
        for category_url, category in self.url_category_list:
            meta = {
                "category": category,
                "category_url_fmt": category_url + "?trang={}",
                "page_idx": page_idx
            }
            category_url = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(category_url, self.parse_category, meta=meta, errback=self.errback)

    def parse_category(self, response):
        meta = dict(response.meta)

        # Navigate to item
        li_elms = response.css("li.pl18-item-li")
        items = []
        for li in li_elms:
            brand = li.css(".pl18-item-brand ::text").extract_first().strip()
            names = li.css(".pl18-item-name ::text").extract()
            names = [name.strip() for name in names]
            model = " ".join(names).strip()
            url = self.base_url + li.css(".pl18-item-name a::attr(href)").extract_first()

            items.append(dict(brand=brand, model=model, url=url))

        self.logger.info("Parse url {}, Num item urls : {}".format(response.url, len(items)))
        for item in items:
            item_url = item.get("url")
            if utils.is_valid_url(item_url):
                item.update({"category": meta["category"]})
                yield Request(item_url, self.parse_item, meta=item, errback=self.errback)

        # Navigate to next page
        if meta["page_idx"] < self.page_per_category_limit and len(items) > 0:
            meta["page_idx"] += 1
            next_page = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(next_page, self.parse_category, meta=meta, errback=self.errback)

    def parse_item(self, response):
        url = response.url
        meta = response.meta
        category = meta["category"]
        brand = meta["brand"]
        model = meta["model"]

        price = response.css("ul.pdt-ul-price div[itemprop=price]::attr(content)").extract_first().strip()

        intro = response.css("div.pdtl-des ::text").extract()
        intro = ". ".join(intro)
        intro = re.sub("\s+", " ", intro)

        info = response.css("div.pd-info-left ::text").extract()
        info = ". ".join([elm.strip() for elm in info])
        info = re.sub("\s+", " ", info)

        info = intro + ". " + info

        self.item_scraped_count += 1
        if self.item_scraped_count % 100 == 0:
            self.logger.info("Spider {}: Crawl {} items".format(self.name, self.item_scraped_count))

        yield Product(
            domain=self.allowed_domains[0],
            product_id="",
            url=url,
            brand=brand,
            category=category,
            model=model,
            info=info,
            price=price,
            seller="",
            reviews=[],
            ratings={}
        )

    def errback(self, failure):
        self.logger.error("Error when send requests : ", failure.request)
