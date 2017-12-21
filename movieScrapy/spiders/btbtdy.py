# -*- coding: UTF-8 -*-
import urllib

import pymysql
import re
import scrapy
from builtins import list, print

from functools import reduce
from requests import request
from scrapy.selector import Selector
# 读取配置文件相关
from scrapy.utils.project import get_project_settings
from movieScrapy.items import XunleipuMovieItem, BtbtdyMovieItem

'''
爬取btbtdy 网站相关功能
'''


class BtbtdySpider(scrapy.Spider):
    name = "btbtdy"

    # 每一个 spider 设置不一样的 pipelines
    custom_settings = {
        'ITEM_PIPELINES': {
            'movieScrapy.pipelines.BtbtMoviescrapyPipeline': 100,
        },
        'DOWNLOAD_DELAY': 10
    }

    def __init__(self, *args, **kwargs):
        super(BtbtdySpider, self).__init__(*args, **kwargs)
        setting = get_project_settings()
        dbargs = dict(
            host=setting.get('MYSQL_HOST'),
            port=3306,
            user=setting.get('MYSQL_USER'),
            password=setting.get('MYSQL_PASSWD'),
            db=setting.get('MYSQL_DBNAME'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )
        self.conn = pymysql.connect(**dbargs)
        self.base_url = 'http://www.btbtdy.com/'
        self.downloadlink_url = 'http://www.btbtdy.com/vidlist/%s.html'
        self.region = {
            '1': '欧美电影',
            '2': '日韩电影',
            '3': '港台电影',
            '4': '大陆电影',
            '5': '经典电影',
            '6': '印度电影',
            '7': '其他电影',
            '8': '泰国电影',
        }

    def start_requests(self):
        '''
        首先获取
        :return:
        '''
        spider_urls = {
            'dianying': {
                'url': 'http://www.btbtdy.com/btfl/dy1-%s.html',
                'start_url': 'http://www.btbtdy.com/btfl/dy1.html',
                'type': 'dy'
            }
        }

        '''
        首先获取第一页 然后获取总的数量 用来判断总共多少页面
        '''
        # item = BtbtdyMovieItem()
        # request = scrapy.Request(url='http://www.btbtdy.com/vidlist/11732.html', callback=self.parse_downloadlink)
        # request.meta['item'] = item
        # yield request

        for i in spider_urls:
            start_url = spider_urls[i]['start_url']
            url = spider_urls[i]['url']
            request = scrapy.Request(url=start_url, callback=self.parse)
            request.meta['url'] = url
            yield request

    def parse(self, response):
        sel = Selector(response)
        # 首先解析出第一页的页面信息
        start_url = response.meta['url']
        sel = Selector(response)
        lis = sel.xpath('/html/body/*[contains(@class,"list_su")]/ul/li')
        for li in lis:
            item = BtbtdyMovieItem()
            title = li.xpath('*[contains(@class,"cts_ms")]/*[contains(@class,"title")]/a')
            href = title.xpath('@href').extract_first()
            text = title.xpath('text()').extract_first()
            item['coversrc'] = li.xpath('*[contains(@class,"liimg")]/a/img/@data-src').extract_first()
            item['title'] = text.strip()
            item['name'] = item['title']
            if self.get_movie(item['title']) is None:
                # 获取详细内容页面 的url 使用相对路径跟绝对路径
                item['region_id'] = 0
                item['region_name'] = ''
                if href:
                    # 截取movie_id 出来
                    movie_id = href[8:href.find('.html')]
                    # print(movie_id)
                    # 把相对路径转换为绝对路径
                    href = urllib.parse.urljoin(start_url, href)
                    item['href'] = href
                    request = scrapy.Request(url=href, callback=self.parse_content)
                    request.meta['item'] = item
                    request.meta['id'] = movie_id
                    yield request
            else:
                print('**********************************')
                print(item['title'] + '电影已经存在，放弃爬取数据')
                print('**********************************')
        # for i in range(2, 4):
        #     url = start_url % i
        #     request = scrapy.Request(url=url, callback=self.parse_list)
        #     yield request

    def get_movie(self, title):
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM movie_btbtdy_list where title like '%" + title + "%'")
        return cur.fetchone()

    def parse_list(self, response):
        '''
        解析列表
        :param response:
        :return:
        '''
        sel = Selector(response)
        lis = sel.xpath(
            '//*[@id="main"]/*[contains(@class,"col4")]/*[contains(@class,"box")]/*[contains(@class,"list")]/li')
        for li in lis:
            item = XunleipuMovieItem()
            title = li.xpath('a')
            href = title.xpath('@href').extract_first()
            text = title.xpath('text()').extract_first()
            if text is None:
                text = title.xpath('font/text()').extract_first()
            item['title'] = text.strip()
            if self.get_movie(item['title']) is None:
                item['region_id'] = 0
                item['region_name'] = ''
                # 获取详细内容页面 的url 使用相对路径跟绝对路径
                if href:
                    # 把相对路径转换为绝对路径
                    item['href'] = href
                    request = scrapy.Request(url=href, callback=self.parse_content)
                    request.meta['item'] = item
                    yield request
            else:
                print('**********************************')
                print(item['title'] + '电影已经存在，放弃爬取数据')
                print('**********************************')

    def subhtml(self, html):
        dr = re.compile(r'<[^>]+>', re.S)
        return dr.sub('', html)

    def parse_content(self, response):
        '''
        解析页面的内容 解析每一个页面的数据
        '''
        item = response.meta['item']
        id = response.meta['id']
        sel = Selector(response)
        # 这个地方要修改 为
        content = sel.xpath(
            '/html/body/*[contains(@class,"topur")]/*[contains(@class,"play")]/*[contains(@class,"vod")]/*[contains(@class,"vod_intro")]')
        ages = content.xpath('h1/span/text()').extract_first()
        item['ages'] = ages[2:len(ages) - 1]
        des = content.xpath('string(.//*[@class="des"])').extract_first()
        item['summary'] = des.replace('剧情介绍：', '').replace(u'\u3000', u'')
        field = content.xpath('dl').extract_first()
        # 清除空格 清除 &nbsp;
        field = field.replace(u'\u3000', u'').replace(u'\xa0', u'')
        fieldlist = field.split('</dd>')
        fieldslist = list(map(self.subhtml, fieldlist))
        item['country'] = country = fieldslist[3].replace('地区:', '')
        item['type'] = fieldslist[2].replace('类型:电影', '').replace(' ', '')
        item['language'] = fieldslist[4].replace('语言:', '')
        item['starring'] = fieldslist[6].replace('主演:', '')
        item['content'] = reduce(lambda x, y: x + '<br/>' + y, fieldslist) + '<br/>' + des
        if country == '大陆':
            item['region_id'] = '4'
            item['region_name'] = '大陆电影'
        elif country == '香港' or country == '台湾':
            item['region_id'] = '3'
            item['region_name'] = '港台电影'
        elif country == '日本' or country == '韩国':
            item['region_id'] = '2'
            item['region_name'] = '日韩电影'
        elif country == '欧美':
            item['region_id'] = '1'
            item['region_name'] = '欧美电影'
        elif country == '泰国':
            item['region_id'] = '8'
            item['region_name'] = '泰国电影'
        elif country == '印度':
            item['region_id'] = '6'
            item['region_name'] = '印度电影'
        # 接下来新发起一个请求 请求下下载链接
        url = self.downloadlink_url % id
        request = scrapy.Request(url=url, callback=self.parse_downloadlink)
        request.meta['item'] = item
        yield request

    def parse_downloadlink(self, response):
        item = response.meta['item']
        sel = Selector(response)
        downloadlist = sel.xpath('//div[@class="p_list"]')
        a_download_info = []
        for perdownload in downloadlist:
            lis = perdownload.xpath('ul/li')
            for li in lis:
                text = li.xpath('a/text()').extract_first()
                link = li.xpath('.//a[contains(@href,"magnet:")]/@href').extract_first()
                type_id = 1
                type_name = '磁力下载'
                a_download_info.append(
                    {'href': link, 'pwd': '', 'text': text, 'type_id': type_id, 'type_name': type_name})
        item['download_a'] = a_download_info
        return item
