from scrapy import Request
from Product_Crawler.spiders.ProductSpider import ProductSpider
from Product_Crawler.items import Product
from Product_Crawler import utils
import re


class MediamartSpider(ProductSpider):
    name = "Mediamart"
    allowed_domains = ["mediamart.vn"]
    base_url = "https://mediamart.vn"

    url_category_list = [
        # ("https://mediamart.vn/may-giat/", "Máy giặt"),
        # ("https://mediamart.vn/smartphones/", "Điện thoại di động"),
        # ("https://mediamart.vn/dien-thoai-di-dong-thuong/", "Điện thoại di động thường"),
        # ("https://mediamart.vn/may-tinh-bang/", "Máy tính bảng"),
        # ("https://mediamart.vn/laptop/", "Laptop"),
        # ("https://mediamart.vn/may-tinh-de-ban/", "Máy tính để bàn"),
        # ("https://mediamart.vn/may-anh-ky-thuat-so/", "Máy ảnh kỹ thuật số"),
        # ("https://mediamart.vn/tivi/", "Tivi"),
        # ("https://mediamart.vn/dan-am-thanh/", "Dàn âm thanh"),
        # ("https://mediamart.vn/soundbar/", "Loa Soundbar"),
        # ("https://mediamart.vn/karaoke/", "Karaoke"),
        # ("https://mediamart.vn/dau-dia/", "Đầu đĩa"),
        # ("https://mediamart.vn/loa-keo-loa-one-box/", "Loa kéo Loa Onebox"),
        # ("https://mediamart.vn/amply/", "Amply"),
        # ("https://mediamart.vn/dau-phat-hd/", "Đầu phát HD"),
        # ("https://mediamart.vn/truyen-hinh-so/", "Truyền hình số"),
        # ("https://mediamart.vn/micro/", "Micro"),
        # ("https://mediamart.vn/cable/", "Cable"),
        # ("https://mediamart.vn/gia-treo/", "Giá treo thiết bị điện tử"),
        # ("https://mediamart.vn/tu-lanh/", "Tủ lạnh"),
        # ("https://mediamart.vn/tu-dong/", "Tủ đông"),
        # ("https://mediamart.vn/tu-lam-mat/", "Tủ làm mát"),
        # ("https://mediamart.vn/may-giat/", "Máy giặt"),
        # ("https://mediamart.vn/may-say-quan-ao/", "Máy sấy quần áo"),
        # ("https://mediamart.vn/dieu-hoa-nhiet-do/", "Điều hòa nhiệt độ"),
        # ("https://mediamart.vn/binh-tam-nong-lanh/", "Bình tắm nóng lạnh"),
        # ("https://mediamart.vn/may-cham-cong/", "Máy chấm công"),
        # ("https://mediamart.vn/may-fax/", "Máy fax"),
        # ("https://mediamart.vn/may-dem-tien/", "Máy đếm tiền"),
        # ("https://mediamart.vn/may-huy-tai-lieu/", "Máy hủy tài liệu"),
        # ("https://mediamart.vn/bo-luu-dien-ups/", "Bộ lưu điện"),
        # ("https://mediamart.vn/may-in/", "Máy in"),
        # ("https://mediamart.vn/may-chieu/", "Máy chiếu"),
        # ("https://mediamart.vn/may-phat-dien/", "Máy phát điện"),
        # ("https://mediamart.vn/may-loc-nuoc/", "Máy lọc nước"),
        # ("https://mediamart.vn/may-nghe-nhac/", "Máy nghe nhạc"),
        # ("https://mediamart.vn/may-loc-khong-khi/", "Máy lọc không khí"),
        # ("https://mediamart.vn/may-hut-bui/", "Máy hút bụi"),
        # ("https://mediamart.vn/may-hut-am/", "Máy hút ẩm"),
        # ("https://mediamart.vn/may-photocopy/", "Máy Photocopy"),
        # ("https://mediamart.vn/may-hut-khoi-hut-mui/", "Máy hút mùi"),
        # ("https://mediamart.vn/may-xay-sinh-to/", "Máy xay sinh tố"),
        # ("https://mediamart.vn/may-ep-vat-trai-cay/", "Máy ép vắt trái cây"),
        # ("https://mediamart.vn/may-danh-trung/", "Máy đánh trứng"),
        # ("https://mediamart.vn/may-lam-sua-dau-nanh/", "Máy làm sữa đậu nành"),
        # ("https://mediamart.vn/may-lam-sua-chua/", "Máy làm sữa chua"),
        # ("https://mediamart.vn/may-pha-ca-phe/", "Máy pha cà phê"),
        # ("https://mediamart.vn/may-vat-cam/", "Máy vắt cam"),
        # ("https://mediamart.vn/may-xay-thit", "Máy xay thịt"),
        ("https://mediamart.vn/quatsuoi/", "Quạt sưởi"),
        ("https://mediamart.vn/quat-dieu-hoa/", "Quạt điều hòa"),
        ("https://mediamart.vn/quat/", "Quạt"),
        ("https://mediamart.vn/ban-la/", "Bàn là"),
        ("https://mediamart.vn/cssk/?loc=may-cao-rau", "Máy cạo râu"),
        # ("", ""),
        # ("", ""),
    ]

    def __init__(self):
        super().__init__(name=self.name)

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
        self.print_num_scraped_items(every=20)

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
