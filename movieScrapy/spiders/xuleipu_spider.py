import base64
from builtins import print
from math import ceil
from urllib.parse import urlparse

import pymysql
import re
import scrapy
from scrapy.selector import Selector
# 读取配置文件相关
from scrapy.utils.project import get_project_settings
from scrapy.utils.response import get_base_url
from twisted.conch.test.test_recvline import down

from movieScrapy.items import XunleipuMovieItem
from urllib import parse


class XunleipuSpider(scrapy.Spider):
    name = "xunleipu"

    # 每一个 spider 设置不一样的 pipelines
    custom_settings = {
        'ITEM_PIPELINES': {
            'movieScrapy.pipelines.MoviescrapyPipeline': 100,
        }
    }

    def __init__(self, *args, **kwargs):
        super(XunleipuSpider, self).__init__(*args, **kwargs)
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
        self.base_url = 'http://www.xlpu.cc'

    def start_requests(self):
        '''
        首先获取
        :return:
        '''
        spider_urls = {
            'oumei': {
                'url': 'http://www.xlpu.cc/category/1_%s.htm',
                'start_url': 'http://www.xlpu.cc/category/1_1.htm',
                'id': 1,
                'name': '欧美电影'
            },
            # 'rihan': {
            #     'url': 'http://www.xlpu.cc/category/2_%s.htm',
            #     'start_url': 'http://www.xlpu.cc/category/2_1.htm',
            #     'id': 2,
            #     'name': '日韩电影'
            # },
            # 'gangtai': {
            #     'url': 'http://www.xlpu.cc/category/3_%s.htm',
            #     'start_url': 'http://www.xlpu.cc/category/3_1.htm',
            #     'id': 3,
            #     'name': '港台电影'
            # },
            # 'dalu': {
            #     'url': 'http://www.xlpu.cc/category/4_%s.htm',
            #     'start_url': 'http://www.xlpu.cc/category/4_1.htm',
            #     'id': 4,
            #     'name': '大陆电影'
            # },
            # 'classics': {
            #     'url': 'http://www.xlpu.cc/category/11_%s.htm',
            #     'start_url': 'http://www.xlpu.cc/category/11_1.htm',
            #     'id': 5,
            #     'name': '经典电影'
            # },
        }

        '''
        首先获取第一页 然后获取总的数量 用来判断总共多少页面
        '''
        for i in spider_urls:
            start_url = spider_urls[i]['start_url']
            id = spider_urls[i]['id']
            name = spider_urls[i]['name']
            url = spider_urls[i]['url']
            request = scrapy.Request(url=start_url, callback=self.parse)
            request.meta['category'] = {'id': id, 'name': name, 'url': url}
            yield request

    def parse(self, response):
        sel = Selector(response)
        #  这个地方有问题  http://www.xlpu.cc/category/1_1.htm   应该获取的是 根目录
        #  首先知道 总共有多少
        #  从谷歌中提取的xpath链接 需要排除出 tbody
        alllist_count = int(
            sel.xpath('//*[@id="classpage2"]/div[5]/table/tr[21]/td/table/tr/td/font[3]/text()').extract_first())
        page_num = ceil(alllist_count / 20)
        # 总的页面数量
        print(alllist_count)
        # 页面num
        print(page_num)
        # 首先解析出第一页的页面信息
        category = response.meta['category']
        sel = Selector(response)
        trs = sel.xpath('//*[@id="classpage2"]/div[5]/table/tr')
        i = 1
        for tr in trs:
            item = XunleipuMovieItem()
            title = tr.xpath('string(td[1]/a)').extract_first()
            item['title'] = title.replace(str(i), '', 1).strip()
            item['addtime'] = tr.xpath('string(td[2])').extract_first()
            item['region_id'] = category['id']
            item['region_name'] = category['name']
            # 获取详细内容页面 的url 使用相对路径跟绝对路径
            relative_href = tr.xpath('td[1]/a/@href').extract_first()
            i = i + 1
            if relative_href:
                href = self.base_url + relative_href
                item['href'] = href
                request = scrapy.Request(url=href, callback=self.parse_content)
                request.meta['item'] = item
                print(item)
                print(href)
                yield request
        category = response.meta['category']
        start_url = category['url']

        # for i in range(2, page_num + 1):
        for i in range(2, 70):
            url = start_url % i
            request = scrapy.Request(url=url, callback=self.parse_list)
            request.meta['category'] = category
            yield request

    def parse_list(self, response):
        '''
        解析列表
        :param response:
        :return:
        '''
        category = response.meta['category']
        sel = Selector(response)
        trs = sel.xpath('//*[@id="classpage2"]/div[5]/table/tr')
        i = 1
        for tr in trs:
            item = XunleipuMovieItem()
            title = tr.xpath('string(td[1]/a)').extract_first()
            item['title'] = title.replace(str(i), '', 1).strip()
            item['addtime'] = tr.xpath('string(td[2])').extract_first()
            item['region_id'] = category['id']
            item['region_name'] = category['name']
            # 获取详细内容页面 的url 使用相对路径跟绝对路径
            relative_href = tr.xpath('td[1]/a/@href').extract_first()
            i = i + 1
            if relative_href:
                if '..' in relative_href:
                    relative_href = relative_href.replace('..', '', 1)
                href = self.base_url + relative_href
                item['href'] = href
                request = scrapy.Request(url=href, callback=self.parse_content)
                request.meta['item'] = item
                print(item)
                print(href)
                yield request

    def parse_content(self, response):
        '''
        解析页面的内容
        '''
        item = response.meta['item']
        sel = Selector(response)
        content_sel = sel.xpath('//*[@id="classpage2"]/div[6]/div[1]/p')
        download_link_a = content_sel.xpath('a')
        a_download_info = []
        for a in download_link_a:
            href = a.xpath('@href').extract_first()
            text = a.xpath('text()').extract_first()
            if 'magnet:' in href:
                type_id = 1
                type_name = '磁力下载'
            elif 'ed2k://' in href:
                type_id = 2
                type_name = '电驴下载'
            elif 'ftp://' in href:
                type_id = 3
                type_name = '迅雷下载'
            elif '' in href:
                type_id = 4
                type_name = '百度云'
                # 百度云链接的话需要密码  这种情况下需要自己进行操作 获取密码
            a_download_info.append({'href': href, 'pwd': '', 'text': text, 'type_id': type_id, 'type_name': type_name})
        item['download_a'] = a_download_info
        # 提取处内容来
        content = ''
        for content_p in content_sel:
            content = content + content_p.extract()
        # 提取处图片来
        replace_pattern = r'<[img|IMG].*?>'  # img标签的正则式
        img_url_pattern = r'.+?src="(\S+)"'  # img_url的正则式
        need_replace_list = re.findall(replace_pattern, content)  # 找到所有的img标签
        img_list = []
        for tag in need_replace_list:
            img_list.append(re.findall(img_url_pattern, tag)[0])  # 找到所有的img_url
        item['imglist'] = img_list
        # 过滤掉 img
        return self.sub_content(content, item, a_download_info)

    def sub_content(self, content, item, a_download_info):
        '''
        截取相关电影的内容
        :return:
        '''
        all_field = [
            {'text': '片名', 'field': 'name'},
            {'text': '译名', 'field': 'alias_name'},
            {'text': '又名', 'field': 'alias_name'},
            {'text': '年代', 'field': 'ages'},
            {'text': '产地', 'field': 'country'},
            {'text': '类别', 'field': 'type'},
            {'text': '类型', 'field': 'type'},
            {'text': '语言', 'field': 'language'},
            {'text': '字幕', 'field': 'subtitle'},
            {'text': '上映日期', 'field': 'releasedate'},
            {'text': 'IMDb评分', 'field': 'imdbscore'},
            {'text': 'IMDB', 'field': 'imdburl'},
            {'text': 'IMDb链接', 'field': 'imdburl'},
            {'text': '豆瓣评分', 'field': 'doubanscore'},
            {'text': '豆瓣链接', 'field': 'doubanurl'},
            {'text': '文件格式', 'field': 'filetype'},
            {'text': '视频尺寸', 'field': 'screensize'},
            {'text': '文件大小', 'field': 'filesize'},
            {'text': '片长', 'field': 'length'},
            {'text': '时长', 'field': 'length'},
            {'text': '主演', 'field': 'starring'},
            {'text': '导演', 'field': 'director'},
            {'text': '简介', 'field': 'summary'}
        ]
        dr = re.compile(r'<[^>]+>', re.S)
        pre_content = content
        # 去除html 标签
        content = dr.sub('', content)
        # 清除空格
        content = content.replace(u'\u3000', u'')
        # item['content'] = self.replace_str(content, a_download_info)
        item['content'] = pre_content
        content_list = content.split('◎')
        # print(')))))))))))))))))))))))))))))))))))))))))))))')
        # print(content_list)
        # print(')))))))))))))))))))))))))))))))))))))))))))))')
        if len(content_list) < 2:
            '''
            解析数据异常
            '''
            return item
        for content_field in content_list:
            # 清除\r\n
            content_field = content_field.strip(' \t\n\r')
            # print('//////////////////')
            # print(content_field)
            # print('//////////////////')
            if not content_field:
                continue
            for field in all_field:
                if field['text'] in content_field:
                    if '简介' == field['text']:
                        # print('))))))))))))))))))))))))))))))')
                        # print(content_field)
                        # print('))))))))))))))))))))))))))))))')
                        content_field = self.replace_str(content_field, a_download_info)
                    fieldtext = content_field.replace(field['text'], '')
                    if field['text'] != '简介' and field['text'] != '主演' and len(fieldtext) > 100:
                        break
                    item[field['field']] = fieldtext.strip(' \t\n\r')
        # 如果是空的字段需要置为空的字段
        for content_field in all_field:
            if not content_field['field'] in item.keys():
                item[content_field['field']] = ''
        return item

    def replace_str(self, content_field, a_download_info):
        content_field = content_field.replace('下载地址', '')
        for pre_a_info in a_download_info:
            content_field = content_field.replace(pre_a_info['text'], '')
        for ch in ['迅雷：', '电驴：', '磁力：', '网盘链接：', '密码：', '迅雷', '电驴', '磁力', '网盘链接', '密码', '\r\n']:
            if ch in content_field:
                content_field = content_field.replace(ch, "")
        return content_field
