# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item


class Product(Item):
    domain = Field()
    product_id = Field()
    url = Field()
    brand = Field()
    category = Field()
    model = Field()
    price = Field()
    seller = Field()
    tags = Field()
    info = Field()
    others = Field()
    ratings = Field()
    reviews = Field()
