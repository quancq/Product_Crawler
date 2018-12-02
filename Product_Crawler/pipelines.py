# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


from Product_Crawler import utils
import os, math, re
from scrapy.exceptions import DropItem
import pandas as pd


class SaveFilePipeline(object):

    def __init__(self):
        # self.file_chunk_size = utils.get_file_chunk_size()
        self.time_now_str = utils.get_time_str()
        self.base_dir = "./Data/Archive"
        self.data = {}
        self.export_format = utils.get_export_format_setting()
        # self.export_fields = utils.get_export_fields_setting()

    def open_spider(self, spider):
        self.data.update({spider.name: {}})

    def process_item(self, item, spider):
        # Append data to collection to finally save to chunk files
        category = item.get("category")
        map_category_items = self.data.get(spider.name)
        items = map_category_items.get(category)
        if items is None:
            items = []
            map_category_items.update({category: items})
        items.append(dict(item))

        return item

    def close_spider(self, spider):
        # Save all items scrapped by spider
        spider_name = spider.name
        map_category_items = self.data.get(spider_name)
        # spider_save_dir = os.path.join(self.save_dir, spider_name)
        for category, items in map_category_items.items():
            category_save_dir = os.path.join(self.base_dir, spider_name, category)
            utils.mkdirs(category_save_dir)
            prefix_fname = "{}_{}".format(spider_name, self.time_now_str)

            # Save items with format setting
            self.save_data(items, category_save_dir, prefix_fname, spider.logger)

    def save_data(self, items, save_dir, prefix_fname, logger):
        if self.export_format == "json":
            save_path = os.path.join(save_dir, "{}_{}items.json".format(
                prefix_fname, len(items)))
            utils.save_json(items, save_path)
        else:
            items_df, ratings_df, reviews_df = [], [], []
            for item in items:
                domain, url = item.get("domain", ""), item.get("url", "")
                product_id, brand = item.get("product_id", ""), item.get("brand", "")
                category, model = item.get("category", ""), item.get("model", "")
                price, seller = item.get("price", ""), item.get("seller", "")
                info = item.get("info", "")

                items_df.append((domain, url, product_id, brand,
                                 category, model, price, seller, info))

                ratings = item["ratings"]
                ratings_df.append((domain, url, product_id, ratings.get(1, 0),
                                   ratings.get(2, 0), ratings.get(3, 0),
                                   ratings.get(4, 0), ratings.get(5, 0)))

                reviews = item["reviews"]
                for review in reviews:
                    reviews_df.append((domain, url, product_id, review.get("rating", ""),
                                       review.get("comment", ""), review.get("review_time", ""),
                                       review.get("bought_time", "")))

            # Save items
            columns = ["Domain", "Url", "Product_id", "Brand", "Category",
                       "Model", "Price", "Seller", "Info"]
            items_df = pd.DataFrame(items_df, columns=columns)
            save_path = os.path.join(save_dir, "{}_{}items.csv".format(
                prefix_fname, items_df.shape[0]))
            utils.save_csv(items_df, save_path)

            # Save ratings
            columns = ["Domain", "Url", "Product_id", "1", "2", "3", "4", "5"]
            ratings_df = pd.DataFrame(ratings_df, columns=columns)
            save_path = os.path.join(save_dir, "{}_{}ratings.csv".format(
                prefix_fname, ratings_df.shape[0]))
            utils.save_csv(ratings_df, save_path)

            # Save reviews
            columns = ["Domain", "Url", "Product_id", "Rating",
                       "Comment", "Review Time", "Bought Time"]
            reviews_df = pd.DataFrame(reviews_df, columns=columns)
            save_path = os.path.join(save_dir, "{}_{}reviews.csv".format(
                prefix_fname, reviews_df.shape[0]))
            utils.save_csv(reviews_df, save_path)

        logger.info("Save {} items to {} done".format(len(items), save_dir))
