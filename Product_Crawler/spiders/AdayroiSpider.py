from scrapy import Request
from Product_Crawler.spiders.ProductSpider import ProductSpider
from Product_Crawler.items import Product
from Product_Crawler import utils
import re
import json
from lxml import html


class AdayroiSpider(ProductSpider):
    name = "Adayroi"
    allowed_domains = ["adayroi.com"]
    base_url = "https://www.adayroi.com"

    url_category_list = [
        # ("https://www.adayroi.com/sua-kem-san-pham-tu-sua-c617", "Sữa và sản phẩm từ sữa"),
        # ("https://www.adayroi.com/bo-c628", "Bơ"),
        # ("https://www.adayroi.com/sua-chua-c625", "Sữa chua"),
        # ("https://www.adayroi.com/kem-c636", "Kem"),
        # ("https://www.adayroi.com/pho-mai-c631", "Phô mai"),
        # ("https://www.adayroi.com/vang-sua-c3325600172153033", "Váng sữa"),
        # ("https://www.adayroi.com/sua-bot-c624", "Sữa bột"),
        # ("https://www.adayroi.com/sua-tuoi-c618", "Sữa tươi"),
        ("https://www.adayroi.com/rau-cu-qua-c639", "Rau củ quả"),
        ("https://www.adayroi.com/do-hop-c664", "Đồ hộp"),
        ("https://www.adayroi.com/thuc-pham-tuoi-c595", "Thực phẩm tươi"),
        ("https://www.adayroi.com/keo-c3325600174461076", "Kẹo"),
        ("https://www.adayroi.com/thuc-pham-an-lien-c671", "Thực phẩm ăn liền"),
        ("https://www.adayroi.com/banh-c697", "Bánh"),
        # ("", ""),
    ]

    def __init__(self):
        super().__init__(name=self.name)

    def start_requests(self):
        page_idx = 0
        for category_url, category in self.url_category_list:
            meta = {
                "category": category,
                "category_url_fmt": category_url + "?page={}",
                "page_idx": page_idx
            }
            category_url = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(category_url, self.parse_category, meta=meta, errback=self.errback)

    def parse_category(self, response):
        meta = dict(response.meta)

        # Navigate to item
        item_urls = response.css("div.product-item a.product-item__thumbnail::attr(href)").extract()

        self.logger.info("Parse url {}, Num item urls : {}".format(response.url, len(item_urls)))
        for item_url in item_urls:
            item_url = self.base_url + item_url
            if utils.is_valid_url(item_url):
                yield Request(item_url, self.parse_item, meta=meta, errback=self.errback)

        # Navigate to next page
        if (meta["page_idx"] + 1) < self.page_per_category_limit and len(item_urls) > 0:
            meta["page_idx"] += 1
            next_page = meta["category_url_fmt"].format(meta["page_idx"])
            yield Request(next_page, self.parse_category, meta=meta, errback=self.errback)

    def parse_item(self, response):
        url = response.url
        meta = response.meta
        category = meta["category"]

        try:
            product_id = re.match(".*-(.*).offer=.*", url).group(1)
        except:
            product_id = ""
        brand_seller_text = response.css(".product-detail__title-brand>a::text").extract()
        if len(brand_seller_text) > 0:
            brand = brand_seller_text[0]
        else:
            brand = ""
        if len(brand_seller_text) > 1:
            seller = brand_seller_text[1].strip().replace(":\xa0", "")
        else:
            seller = ""
        model = response.css(".product-detail__title>h1::text").extract_first()
        price = response.css(".product-detail__price-info ::text").extract_first()

        intro = response.css(".short-des__content ::text").extract()
        intro = ". ".join(intro)
        intro = re.sub("\s+", " ", intro)

        try:
            specs = response.css(".product-specs__table")[0].css("::text").extract()
            specs = " ".join(specs)
        except:
            specs = ""

        try:
            info = response.css(".product-detail__description ::text").extract()
            info = " ".join([elm.replace("\xa0", "") for elm in info])
            info = re.sub("\s+", " ", info)
        except:
            info = ""

        info = intro + ". " + specs + ". " + info
        tags = response.css(".product-tag__list>a::text").extract()
        tags = ",".join(tags)

        item = dict(product_id=product_id, model=model, category=category, url=url,
                    price=price, brand=brand, seller=seller, tags=tags, info=info)

        # Crawl ratings and reviews
        review_url = response.css(".product-comment__list::attr(data-allreviews)").extract_first()
        review_url = self.base_url + review_url

        yield Request(review_url, self.parse_reviews, meta=item, errback=self.errback)

    def parse_reviews(self, response):
        meta = response.meta
        divs = response.css(".product-comment__item")

        ratings = {r: 0 for r in range(5)}
        reviews = []
        for div in divs:
            try:
                review_time = div.css(".comment-item__time .date::text").extract_first()
                review_time = utils.transform_time_fmt(review_time, src_fmt="%d/%m/%Y %H:%M")

                json_str = div.css(".rating-stars::attr(data-rating)").extract_first()
                json_data = json.loads(json_str)
                rating = int(float(json_data["rating"]))

                comment = div.css(".comment-item__content ::text").extract_first().strip()
                # comment = [c.strip() for c in comment]
                # comment = " ".join(comment)
            except:
                continue

            if rating >= 1:
                curr_count = ratings.get(rating, 0)
                ratings.update({rating: curr_count+1})

                reviews.append(dict(review_time=review_time, rating=rating, comment=comment))

        self.item_scraped_count += 1
        self.print_num_scraped_items(every=20)

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
            tags=meta["tags"],
            reviews=reviews,
            ratings=ratings
        )

    def errback(self, failure):
        self.logger.error("Error when send requests : ", failure.request)
