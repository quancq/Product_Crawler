import scrapy
from Product_Crawler import utils
from Product_Crawler.crawl_proxy import ProxyManager
import requests


class ProductSpider(scrapy.Spider):
    def __init__(self, name=None, **kwargs):
        super(ProductSpider, self).__init__(name=name, **kwargs)
        self.page_per_category_limit = utils.get_crawl_limit_setting(name)
        self.item_scraped_count = 0
        self.pm = ProxyManager(update=True)
        self.pm.save_proxies(mode="au")

    def parse(self, response):
        raise NotImplementedError()

    def parse_category(self, response):
        raise NotImplementedError()

    def parse_item(self, response):
        raise NotImplementedError()

    # def transform_time_fmt(self, time_str, src_fmt):
    #     try:
    #         return utils.transform_time_fmt(time_str, src_fmt=src_fmt)
    #     except:
    #         self.logger.debug("Exception when parse time_str : ", time_str)
    #         return ""

    def get_response(self, url):
        res = self.pm.get_response(url)
        if res is None:
            res = requests.get(url)

        return res
