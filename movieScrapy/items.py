# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MoviescrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class XunleipuMovieItem(scrapy.Item):
    # 网站的标题
    title = scrapy.Field()
    # 电影名称
    name = scrapy.Field()
    # 别名
    alias_name = scrapy.Field()
    # 年代
    ages = scrapy.Field()
    # 产地
    country = scrapy.Field()
    # 类别
    type = scrapy.Field()
    # 语言
    language = scrapy.Field()
    # 字幕
    subtitle = scrapy.Field()
    # 上映日期
    releasedate = scrapy.Field()
    imdbscore = scrapy.Field()
    imdburl = scrapy.Field()
    doubanscore = scrapy.Field()
    doubanurl = scrapy.Field()
    # 文件类型
    filetype = scrapy.Field()
    # 屏幕大小
    screensize = scrapy.Field()
    # 文件大小
    filesize = scrapy.Field()
    # 时长
    length = scrapy.Field()
    # 主演
    starring = scrapy.Field()
    # 导演
    director = scrapy.Field()
    # 简介
    summary = scrapy.Field()
    content = scrapy.Field()
    addtime = scrapy.Field()
    # 区域name
    region_id = scrapy.Field()
    # 区域的name
    region_name = scrapy.Field()
    # 网页的原始链接
    href = scrapy.Field()
    download_a = scrapy.Field()
    # 图片list
    imglist = scrapy.Field()
    # 爬取时间
    scrapytime = scrapy.Field()
