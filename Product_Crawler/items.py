# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item


class Product(Item):
    brand = Field()
    category = Field()
    model = Field()
    url = Field()
    text = Field()
    price = Field()
