# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import random

import time

import pymysql
import requests
from scrapy import signals
from scrapy.utils.project import get_project_settings


class MoviescrapySpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)



class RandomUserAgent(object):
    """Randomly rotate user agents based on a list of predefined ones"""

    def __init__(self, agents):
        self.agents = agents

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist('PC_USER_AGENTS'))

    def process_request(self, request, spider):
        request.headers.setdefault('User-Agent', random.choice(self.agents))


# HTTP 从数据库中随机取数据
class ProxyMiddleware(object):
    def __init__(self):
        # 默认为 http
        self.httppool = (Proxypool()).getDbproxy('HTTP')
        self.httpspool = (Proxypool()).getDbproxy('HTTPS')

    def removeproxy(self, proxy, type):
        '''
        清除掉 已经失效的 http代理数据
        '''
        print('过期过期过期********************')
        print(proxy)
        '''Remove a proxy from pool'''
        if type == 'HTTP':
            if proxy in self.httppool:
                # 从数据库中删除某条记录
                self.httppool.remove(proxy)
                (Proxypool()).removeExpireProxy(proxy)
        else:
            if proxy in self.httpspool:
                self.httpspool.remove(proxy)
                (Proxypool()).removeExpireProxy(proxy)
        print('********************')

    def randomchoose(self, type):
        '''
        随机选择 一个代理使用 如果代理库中的数量为零  或者 10分钟之内 时间没有获取的话
        判断一下是不是超过多长时间没有获取过 代理ip了
        '''
        if type == 'HTTP':
            if not self.httppool:
                return False
            if len(self.httppool) <= 10:
                # 随机获取 ip代理
                # 用芝麻代理获取数据
                self.httppool = (Proxypool()).getDbproxy(type)
                if not self.httppool:
                    return False
                if len(self.httppool) > 0:
                    return random.sample(self.httppool, 1)[0]
                else:
                    return False
            else:
                return random.sample(self.httppool, 1)[0]
        else:
            if not self.httpspool:
                return False
            if len(self.httpspool) <= 10:
                # 随机获取 ip代理
                # 用芝麻代理获取数据
                self.httpspool = (Proxypool()).getDbproxy(type)
                if not self.httpspool:
                    return False
                if len(self.httpspool) > 0:
                    return random.sample(self.httpspool, 1)[0]
                else:
                    return False
            else:
                return random.sample(self.httpspool, 1)[0]

    def getproxy(self, type):
        '''
        返回代理数据 实际上不需要 判断能不能正常请求 只需要从后台获取数据便可
        '''
        proxy = self.randomchoose(type)
        if not proxy:
            return {}
        current_time = int(time.time())
        expire_time = proxy['expire_time']
        if expire_time > current_time:
            return proxy
        else:
            self.removeproxy(proxy, type)
            return self.getproxy(type)

    def process_request(self, request, spider):
        '''
        处理请求数据
        Set the location of the proxy
        request.meta['proxy'] = "http://182.117.207.229:9481"
        :param request:
        :param spider:
        :return:
        '''
        # 从数据库中取出一条来
        # 判断请求的 url 是啥
        type = 'HTTP'
        if request.url.startswith("https://"):
            type = 'HTTPS'
        proxyinfo = self.getproxy(type)
        print('使用代理************************************')
        print(proxyinfo)
        print('************************************')
        if proxyinfo:
            request.meta['proxy'] = "http://" + proxyinfo['ip'] + ":" + str(proxyinfo['port'])


# HTTP 代理
class Proxypool(object):
    '''http代理池 管理 这样的话可以共用'''

    def __init__(self):
        '''
        '''
        self.setting = get_project_settings()
        dbargs = dict(
            host=self.setting.get('MYSQL_HOST'),
            port=3306,
            user=self.setting.get('MYSQL_USER'),
            password=self.setting.get('MYSQL_PASSWD'),
            db=self.setting.get('MYSQL_DBNAME'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )
        self.conn = pymysql.connect(**dbargs)

    def getDbproxy(self, type, dep=0):
        '''
        获取数据库中数据
        :return:
        '''
        if dep >= 2:
            # 防止死循环
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM `movie_zhimadaili_ipproxy` where type='" + type + "'")
            proxy = cursor.fetchall()
            if len(proxy) <= 10:
                # 从远程获取数据
                self.getProxy(type)
                dep = dep + 1
                return self.getDbproxy(type, dep)
            return proxy
        except Exception as e:
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(e)
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print('从数据库获取代理ip 失败')

    def getProxy(self, type):
        '''
        从芝麻代理请求数据
        :return:
        '''
        # http 代理
        cs_url = 'http://http-webapi.zhimaruanjian.com/getip?num=50&type=2&pro=0&city=0&yys=0&port=1&pack=286&ts=1&ys=1&cs=1&lb=1&sb=0&pb=4&mr=1'
        if type == 'HTTPS':
            # 获取 https 代理
            cs_url = 'http://http-webapi.zhimaruanjian.com/getip?num=50&type=2&pro=0&city=0&yys=0&port=11&pack=286&ts=1&ys=1&cs=1&lb=1&sb=0&pb=4&mr=1'
        r = requests.get(cs_url)
        if r.status_code == requests.codes.ok:
            d = r.json()
            current_time = str(int(time.time()))
            if d['code'] == 0:
                data = d['data']
                for proxy in data:
                    try:
                        cursor = self.conn.cursor()
                        # 首先查询下 是不是已经存在这个链接了
                        sql = 'insert into `movie_zhimadaili_ipproxy` (`ip`,`type`,`port`,`isp`,`city`,`expire_time`,`create_time`)values(%s,%s,%s,%s,%s,%s,%s);'
                        expire_time = 0
                        isp = ''
                        city = ''
                        if 'expire_time' in proxy:
                            if proxy['expire_time'] != None:
                                expire_time = int(
                                    time.mktime(time.strptime(proxy['expire_time'], '%Y-%m-%d %H:%M:%S')))
                        if 'isp' in proxy:
                            isp = proxy['isp']
                        if 'city' in proxy:
                            city = proxy['city']
                        cursor.execute(sql, (
                            proxy['ip'], type, proxy['port'], isp, city, str(expire_time),
                            current_time))
                        self.conn.commit()
                    except Exception as e:
                        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                        print(e)
                        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                        print('代理 ip 添加到数据库失败')
            else:
                # 添加到错误表中
                try:
                    cursor = self.conn.cursor()
                    # 首先查询下 是不是已经存在这个链接了
                    sql = 'insert into `movie_ipproxy_error_info` (`msg`,`code`,`create_time`) values(%s,%s,%s);'
                    cursor.execute(sql, (d['msg'], d['code'], current_time))
                    self.conn.commit()
                except Exception as e:
                    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    print(e)
                    print('添加获取代理ip错误信息失败')
                    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

    def removeExpireProxy(self, proxy):
        '''
        删除已经过期的代理
        :param proxy: 代理dict 包含 id 根据
        :return:
        '''
        try:
            id = str(proxy['id'])
            cursor = self.conn.cursor()
            # 首先查询下 是不是已经存在这个链接了
            sql = 'delete from movie_zhimadaili_ipproxy where id=' + id + ';'
            cursor.execute(sql)
            self.conn.commit()
        except Exception as e:
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(e)
            print('删除代理ip数据失败')
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')