# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
import time
from builtins import print
from select import select

import pymysql


class MoviescrapyPipeline(object):
    def __init__(self, conn):
        self.conn = conn

    # 从配置文件中读取数据
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dbargs = dict(
            host=settings.get('MYSQL_HOST'),
            port=3306,
            user=settings.get('MYSQL_USER'),
            password=settings.get('MYSQL_PASSWD'),
            db=settings.get('MYSQL_DBNAME'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )
        connection = pymysql.connect(**dbargs)
        return cls(connection)

    # pipeline默认调用
    def process_item(self, item, spider):
        print(item['title'])
        print(item['download_a'])
        print(item['imglist'])
        if 'name' in item.keys() and item['name'] != '':
            # 正确取到数据
            # 首先取出 封面图片
            currenttime = int(time.time())
            coversrc = ''
            imglist = []
            # 首先从数据库中取出
            for imgsrc in item['imglist']:
                if not coversrc:
                    coversrc = imgsrc
                imglist.append(imgsrc)
            with self.conn.cursor() as cursor:
                # 需要从数据库中 获取 电影的 类型：然后 匹配下电影的分类
                type_info = []
                # 需要从数据库中 获取 电影的 类型：然后 匹配下电影的分类
                sql = "select id,name from movie.movie_type"
                cursor.execute(sql)
                type_info = cursor.fetchall()
                # type 信息
                movietype_info = re.split('/| ', item['type'])
                type_ids_str = ','
                for movietype in movietype_info:
                    # 数据库中爬取的分类
                    if not movietype:
                        break
                    type_id = 0
                    for typedict in type_info:
                        if typedict['name'] in movietype:
                            type_id = typedict['id']
                            break
                    if type_id == 0:
                        # 表示某个字段没有匹配到需要添加到数据库中
                        currenttime = int(time.time())
                        typesql = 'insert into movie_type(`name`,`created_at`) VALUES ("%s","%s")' % (
                            movietype, currenttime)
                        # 分类sql
                        print('????????????????????????????')
                        print(typesql)
                        print('????????????????????????????')
                        cursor.execute(typesql)
                        self.conn.commit()
                        # 然后获取 插入的id 是多少
                        selectsql = 'select id,name from movie.movie_type WHERE name="%s"' % movietype
                        cursor.execute(selectsql)
                        type_id = cursor.fetchone()['id']
                    type_ids_str = type_ids_str + str(type_id) + ','
                print('????????????????????????????///////')
                print(type_ids_str)
                print('????????????????????????????///////')
                sql = 'insert into movie_xunleipu_list (name,alias_name,title,ages,country,type,language,subtitle,releasedate,imdburl,imdbscore,doubanurl,doubanscore,filetype,screensize,filesize,length,starring,director,' \
                      'summary,content,region_id,region_name,create_time,update_time,href,coversrc) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                cursor.execute(sql, (
                    item['name'], item['alias_name'], item['title'], item['ages'], item['country'], type_ids_str, \
                    item['language'], item['subtitle'], item['releasedate'], item['imdburl'], item['imdbscore'], \
                    item['doubanurl'], item['doubanscore'], item['filetype'], item['screensize'], item['filesize'], \
                    item['length'], item['starring'], item['director'], item['summary'],
                    pymysql.escape_string(item['content']), item['region_id'], item['region_name'], currenttime,
                    currenttime, item['href'], coversrc))
                self.conn.commit()
                selectsql = 'select id,name from movie.movie_xunleipu_list WHERE name="%s"' % item['name']
                cursor.execute(selectsql)
                movie_idinfo = cursor.fetchone()
                print(movie_idinfo)
                # 添加电影的下载链接 这块可以单独封装函数
                add_download_sql = 'insert into movie.movie_xunleipu_download_link(movie_id, type_name, type_id,href, text, pwd, create_time, update_time) VALUES '
                templatesql = "(%s,'%s',%s,'%s','%s','%s',%s,%s)"
                insert_sql = ''
                currenttime = int(time.time())
                i = 1
                for download in item['download_a']:
                    download_sql = templatesql % (
                        movie_idinfo['id'], download['type_name'], download['type_id'], download['href'],
                        download['text'], download['pwd'], currenttime,
                        currenttime)
                    if i == 1:
                        insert_sql = download_sql
                    else:
                        insert_sql = insert_sql + ',' + download_sql
                    i = i + 1
                if insert_sql:
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    print(add_download_sql + insert_sql)
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    cursor.execute(add_download_sql + insert_sql)
                    self.conn.commit()
                # 然后添加电影的图片链接 这块可以单独封装函数
                add_img_sql = 'insert into movie.movie_xunleipu_imglist(movie_id,imgsrc,create_time,update_time) VALUES'
                imgtemplatesql = "(%s,'%s',%s,%s)"
                insert_img_sql = ''
                currenttime = int(time.time())
                i = 1
                for img in imglist:
                    img_sql = imgtemplatesql % (
                        movie_idinfo['id'], img, currenttime, currenttime)
                    if i == 1:
                        insert_img_sql = img_sql
                    else:
                        insert_img_sql = insert_img_sql + ',' + img_sql
                    i = i + 1
                if insert_img_sql:
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(add_img_sql + insert_img_sql)
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    cursor.execute(add_img_sql + insert_img_sql)
                    self.conn.commit()
        else:  # 没有取到数据 只报存content 然后手工解析
            '''
            {
             'addtime': '2007/11/23 11:02:00',
             'content': '导演 |Mark Fergus主演 |盖·皮尔斯, 派珀.佩拉勃, 威廉.菲彻特纳, J.K.西蒙, 席.韦格汉姆, Rick '
                        'Gonzalez (I), 杰基.伯勒斯, 亚当.司各特(I), Portia Dawson, Cherilyn Hayres类型 '
                        '|剧情 惊悚&amp;nbsp年份 |2007地区 |德国语言 |英语片长 |101分钟色彩 |彩色 '
                        '电影介绍吉姆是一个推销员，最近却总是有一些倒霉事落到他头上。算命师说他将会有劫难，随着天气逐渐变冷，吉姆越来越害怕另一个预言会实现--在第一场雪落下后，他们的生命也就到了尽头……影片截图::',
             'download_a': [{'href': 'http://movie.gougou.com/search?search=%E7%AC%AC%E4%B8%80%E5%9C%BA%E9%9B%AA&ampampamprestype=4&ampampampid=12',
                             'pwd': '',
                             'text': '点击进入下载页面',
                             'type_id': 4,
                             'type_name': '百度云'}],
             'href': 'http://www.xlpu.cc/html/48.html',
             'imglist': ['http://images.movie.xunlei.com/gallery/389/e1c87e6bc16853f9be993d3492c3742b.jpg',
                         'http://images.movie.xunlei.com/gallery/389/87d32dbe8876617f73c7de73e7f45b84.jpg',
                         'http://images.movie.xunlei.com/gallery/389/d0f586be70999d6ec2ddeb497cf77ae1.jpg',
                         'http://images.movie.xunlei.com/gallery/389/44225ce6a8c0baa891f84d0011b33000.jpg',
                         'http://images.movie.xunlei.com/gallery/389/2608d7ad62127fc079570ce06916a0b5.jpg'],
             'region_id': 1,
             'region_name': '欧美电影',
             'title': '《第一场雪》'}
            '''
            currenttime = int(time.time())
            coversrc = ''
            imglist = []
            # 首先从数据库中取出
            for imgsrc in item['imglist']:
                if not coversrc:
                    coversrc = imgsrc
                else:
                    imglist.append(imgsrc)
            with self.conn.cursor() as cursor:
                sql = "insert into movie.movie_xunleipu_list(title, content, region_id, region_name, update_time, create_time, href, coversrc) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(sql, (
                    item['title'], pymysql.escape_string(item['content']), item['region_id'], item['region_name'],
                    currenttime, currenttime, item['href'], coversrc))
                self.conn.commit()
                selectsql = 'select id,title from movie.movie_xunleipu_list WHERE title="%s"' % item['title']
                cursor.execute(selectsql)
                movie_idinfo = cursor.fetchone()
                print(movie_idinfo)
                # 添加电影的下载链接 这块可以单独封装函数
                add_download_sql = 'insert into movie.movie_xunleipu_download_link(movie_id, type_name, type_id,href, text, pwd, create_time, update_time) VALUES '
                templatesql = "(%s,'%s',%s,'%s','%s','%s',%s,%s)"
                insert_sql = ''
                currenttime = int(time.time())
                i = 1
                for download in item['download_a']:
                    download_sql = templatesql % (
                        movie_idinfo['id'], download['type_name'], download['type_id'], download['href'],
                        download['text'], download['pwd'], currenttime,
                        currenttime)
                    if i == 1:
                        insert_sql = download_sql
                    else:
                        insert_sql = insert_sql + ',' + download_sql
                    i = i + 1
                if insert_sql:
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    print(add_download_sql + insert_sql)
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    cursor.execute(add_download_sql + insert_sql)
                    self.conn.commit()
                # 然后添加电影的图片链接 这块可以单独封装函数
                add_img_sql = 'insert into movie.movie_xunleipu_imglist(movie_id,imgsrc,create_time,update_time) VALUES'
                imgtemplatesql = "(%s,'%s',%s,%s)"
                insert_img_sql = ''
                currenttime = int(time.time())
                i = 1
                for img in imglist:
                    img_sql = imgtemplatesql % (
                        movie_idinfo['id'], img, currenttime, currenttime)
                    if i == 1:
                        insert_img_sql = img_sql
                    else:
                        insert_img_sql = insert_img_sql + ',' + img_sql
                    i = i + 1
                if insert_img_sql:
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(add_img_sql + insert_img_sql)
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    cursor.execute(add_img_sql + insert_img_sql)
                    self.conn.commit()


class dyttMoviescrapyPipeline(object):
    def __init__(self, conn):
        self.conn = conn

    # 从配置文件中读取数据
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dbargs = dict(
            host=settings.get('MYSQL_HOST'),
            port=3306,
            user=settings.get('MYSQL_USER'),
            password=settings.get('MYSQL_PASSWD'),
            db=settings.get('MYSQL_DBNAME'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )
        connection = pymysql.connect(**dbargs)
        return cls(connection)

    # pipeline默认调用
    def process_item(self, item, spider):
        print(item['title'])
        print(item['download_a'])
        print(item['imglist'])
        if 'name' in item.keys() and item['name'] != '':
            # 正确取到数据
            # 首先取出 封面图片
            currenttime = int(time.time())
            coversrc = ''
            imglist = []
            # 首先从数据库中取出
            for imgsrc in item['imglist']:
                if not coversrc:
                    coversrc = imgsrc
                else:
                    imglist.append(imgsrc)
            with self.conn.cursor() as cursor:
                # 需要从数据库中 获取 电影的 类型：然后 匹配下电影的分类
                type_info = []
                # 需要从数据库中 获取 电影的 类型：然后 匹配下电影的分类
                sql = "select id,name from movie.movie_type"
                cursor.execute(sql)
                type_info = cursor.fetchall()
                # print(type_info)
                # type 信息
                movietype_info = re.split('/| ', item['type'])
                type_ids_str = ','
                for movietype in movietype_info:
                    # 数据库中爬取的分类
                    if not movietype:
                        break
                    type_id = 0
                    for typedict in type_info:
                        if typedict['name'] in movietype:
                            type_id = typedict['id']
                            break
                    if type_id == 0:
                        # 表示某个字段没有匹配到需要添加到数据库中
                        currenttime = int(time.time())
                        typesql = 'insert into movie_type(`name`,`created_at`) VALUES ("%s","%s")' % (
                            movietype, currenttime)
                        # 分类sql
                        print('????????????????????????????')
                        print(typesql)
                        print('????????????????????????????')
                        cursor.execute(typesql)
                        self.conn.commit()
                        # 然后获取 插入的id 是多少
                        selectsql = 'select id,name from movie.movie_type WHERE name="%s"' % movietype
                        cursor.execute(selectsql)
                        type_id = cursor.fetchone()['id']
                    type_ids_str = type_ids_str + str(type_id) + ','
                print('????????????????????????????///////')
                print(type_ids_str)
                print('????????????????????????????///////')
                sql = 'insert into movie_dytt_list (name,alias_name,title,ages,country,type,language,subtitle,releasedate,imdburl,imdbscore,doubanurl,doubanscore,filetype,screensize,filesize,length,starring,director,' \
                      'summary,content,region_id,region_name,create_time,update_time,href,coversrc) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                cursor.execute(sql, (
                    item['name'], item['alias_name'], item['title'], item['ages'], item['country'], type_ids_str, \
                    item['language'], item['subtitle'], item['releasedate'], item['imdburl'], item['imdbscore'], \
                    item['doubanurl'], item['doubanscore'], item['filetype'], item['screensize'], item['filesize'], \
                    item['length'], item['starring'], item['director'], item['summary'],
                    pymysql.escape_string(item['content']), item['region_id'], item['region_name'], currenttime,
                    currenttime, item['href'], coversrc))
                self.conn.commit()
                selectsql = 'select id,name from movie.movie_dytt_list WHERE name="%s"' % item['name']
                cursor.execute(selectsql)
                movie_idinfo = cursor.fetchone()
                print(movie_idinfo)
                # 添加电影的下载链接 这块可以单独封装函数
                add_download_sql = 'insert into movie.movie_dytt_download_link(movie_id, type_name, type_id,href, text, pwd, create_time, update_time) VALUES '
                templatesql = "(%s,'%s',%s,'%s','%s','%s',%s,%s)"
                insert_sql = ''
                currenttime = int(time.time())
                i = 1
                for download in item['download_a']:
                    download_sql = templatesql % (
                        movie_idinfo['id'], download['type_name'], download['type_id'], download['href'],
                        download['text'], download['pwd'], currenttime,
                        currenttime)
                    if i == 1:
                        insert_sql = download_sql
                    else:
                        insert_sql = insert_sql + ',' + download_sql
                    i = i + 1
                if insert_sql:
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    print(add_download_sql + insert_sql)
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    cursor.execute(add_download_sql + insert_sql)
                    self.conn.commit()
                # 然后添加电影的图片链接 这块可以单独封装函数
                add_img_sql = 'insert into movie.movie_dytt_imglist(movie_id,imgsrc,create_time,update_time) VALUES'
                imgtemplatesql = "(%s,'%s',%s,%s)"
                insert_img_sql = ''
                currenttime = int(time.time())
                i = 1
                for img in imglist:
                    img_sql = imgtemplatesql % (
                        movie_idinfo['id'], img, currenttime, currenttime)
                    if i == 1:
                        insert_img_sql = img_sql
                    else:
                        insert_img_sql = insert_img_sql + ',' + img_sql
                    i = i + 1
                if insert_img_sql:
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(add_img_sql + insert_img_sql)
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    cursor.execute(add_img_sql + insert_img_sql)
                    self.conn.commit()
        else:  # 没有取到数据 只报存content 然后手工解析
            '''
            {
             'addtime': '2007/11/23 11:02:00',
             'content': '导演 |Mark Fergus主演 |盖·皮尔斯, 派珀.佩拉勃, 威廉.菲彻特纳, J.K.西蒙, 席.韦格汉姆, Rick '
                        'Gonzalez (I), 杰基.伯勒斯, 亚当.司各特(I), Portia Dawson, Cherilyn Hayres类型 '
                        '|剧情 惊悚&amp;nbsp年份 |2007地区 |德国语言 |英语片长 |101分钟色彩 |彩色 '
                        '电影介绍吉姆是一个推销员，最近却总是有一些倒霉事落到他头上。算命师说他将会有劫难，随着天气逐渐变冷，吉姆越来越害怕另一个预言会实现--在第一场雪落下后，他们的生命也就到了尽头……影片截图::',
             'download_a': [{'href': 'http://movie.gougou.com/search?search=%E7%AC%AC%E4%B8%80%E5%9C%BA%E9%9B%AA&ampampamprestype=4&ampampampid=12',
                             'pwd': '',
                             'text': '点击进入下载页面',
                             'type_id': 4,
                             'type_name': '百度云'}],
             'href': 'http://www.xlpu.cc/html/48.html',
             'imglist': ['http://images.movie.xunlei.com/gallery/389/e1c87e6bc16853f9be993d3492c3742b.jpg',
                         'http://images.movie.xunlei.com/gallery/389/87d32dbe8876617f73c7de73e7f45b84.jpg',
                         'http://images.movie.xunlei.com/gallery/389/d0f586be70999d6ec2ddeb497cf77ae1.jpg',
                         'http://images.movie.xunlei.com/gallery/389/44225ce6a8c0baa891f84d0011b33000.jpg',
                         'http://images.movie.xunlei.com/gallery/389/2608d7ad62127fc079570ce06916a0b5.jpg'],
             'region_id': 1,
             'region_name': '欧美电影',
             'title': '《第一场雪》'}
            '''
            currenttime = int(time.time())
            coversrc = ''
            imglist = []
            # 首先从数据库中取出
            for imgsrc in item['imglist']:
                if not coversrc:
                    coversrc = imgsrc
                else:
                    imglist.append(imgsrc)
            with self.conn.cursor() as cursor:
                sql = "insert into movie.movie_dytt_list(title, content, region_id, region_name, update_time, create_time, href, coversrc) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(sql, (
                    item['title'], pymysql.escape_string(item['content']), item['region_id'], item['region_name'],
                    currenttime, currenttime, item['href'], coversrc))
                self.conn.commit()
                selectsql = 'select id,title from movie.movie_dytt_list WHERE title="%s"' % item['title']
                cursor.execute(selectsql)
                movie_idinfo = cursor.fetchone()
                print(movie_idinfo)
                # 添加电影的下载链接 这块可以单独封装函数
                add_download_sql = 'insert into movie.movie_dytt_download_link(movie_id, type_name, type_id,href, text, pwd, create_time, update_time) VALUES '
                templatesql = "(%s,'%s',%s,'%s','%s','%s',%s,%s)"
                insert_sql = ''
                currenttime = int(time.time())
                i = 1
                for download in item['download_a']:
                    download_sql = templatesql % (
                        movie_idinfo['id'], download['type_name'], download['type_id'], download['href'],
                        download['text'], download['pwd'], currenttime,
                        currenttime)
                    if i == 1:
                        insert_sql = download_sql
                    else:
                        insert_sql = insert_sql + ',' + download_sql
                    i = i + 1
                if insert_sql:
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    print(add_download_sql + insert_sql)
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    cursor.execute(add_download_sql + insert_sql)
                    self.conn.commit()
                # 然后添加电影的图片链接 这块可以单独封装函数
                add_img_sql = 'insert into movie.movie_dytt_imglist(movie_id,imgsrc,create_time,update_time) VALUES'
                imgtemplatesql = "(%s,'%s',%s,%s)"
                insert_img_sql = ''
                currenttime = int(time.time())
                i = 1
                for img in imglist:
                    img_sql = imgtemplatesql % (
                        movie_idinfo['id'], img, currenttime, currenttime)
                    if i == 1:
                        insert_img_sql = img_sql
                    else:
                        insert_img_sql = insert_img_sql + ',' + img_sql
                    i = i + 1
                if insert_img_sql:
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(add_img_sql + insert_img_sql)
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    cursor.execute(add_img_sql + insert_img_sql)
                    self.conn.commit()


class hao6vMoviescrapyPipeline(object):
    def __init__(self, conn):
        self.conn = conn

    # 从配置文件中读取数据
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dbargs = dict(
            host=settings.get('MYSQL_HOST'),
            port=3306,
            user=settings.get('MYSQL_USER'),
            password=settings.get('MYSQL_PASSWD'),
            db=settings.get('MYSQL_DBNAME'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )
        connection = pymysql.connect(**dbargs)
        return cls(connection)

    # pipeline默认调用
    def process_item(self, item, spider):
        print(item['title'])
        print(item['download_a'])
        print(item['imglist'])
        if 'name' in item.keys() and item['name'] != '':
            # 正确取到数据
            # 首先取出 封面图片
            currenttime = int(time.time())
            coversrc = ''
            imglist = []
            # 首先从数据库中取出
            for imgsrc in item['imglist']:
                if not coversrc:
                    coversrc = imgsrc
                imglist.append(imgsrc)
            with self.conn.cursor() as cursor:
                # 需要从数据库中 获取 电影的 类型：然后 匹配下电影的分类
                type_info = []
                # 需要从数据库中 获取 电影的 类型：然后 匹配下电影的分类
                sql = "select id,name from movie.movie_type"
                cursor.execute(sql)
                type_info = cursor.fetchall()
                # print(type_info)
                # type 信息
                movietype_info = re.split('/| ', item['type'])
                type_ids_str = ','
                for movietype in movietype_info:
                    # 数据库中爬取的分类
                    if not movietype:
                        break
                    type_id = 0
                    for typedict in type_info:
                        if typedict['name'] in movietype:
                            type_id = typedict['id']
                            break
                    if type_id == 0:
                        # 表示某个字段没有匹配到需要添加到数据库中
                        currenttime = int(time.time())
                        typesql = 'insert into movie_type(`name`,`created_at`) VALUES ("%s","%s")' % (
                            movietype, currenttime)
                        # 分类sql
                        print('????????????????????????????')
                        print(typesql)
                        print('????????????????????????????')
                        cursor.execute(typesql)
                        self.conn.commit()
                        # 然后获取 插入的id 是多少
                        selectsql = 'select id,name from movie.movie_type WHERE name="%s"' % movietype
                        cursor.execute(selectsql)
                        type_id = cursor.fetchone()['id']
                    type_ids_str = type_ids_str + str(type_id) + ','
                print('????????????????????????????///////')
                print(type_ids_str)
                print('????????????????????????????///////')
                sql = 'insert into movie_hao6v_list (name,alias_name,title,ages,country,type,language,subtitle,releasedate,imdburl,imdbscore,doubanurl,doubanscore,filetype,screensize,filesize,length,starring,director,' \
                      'summary,content,region_id,region_name,create_time,update_time,href,coversrc) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                cursor.execute(sql, (
                    item['name'], item['alias_name'], item['title'], item['ages'], item['country'], type_ids_str, \
                    item['language'], item['subtitle'], item['releasedate'], item['imdburl'], item['imdbscore'], \
                    item['doubanurl'], item['doubanscore'], item['filetype'], item['screensize'], item['filesize'], \
                    item['length'], item['starring'], item['director'], item['summary'],
                    pymysql.escape_string(item['content']), item['region_id'], item['region_name'], currenttime,
                    currenttime, item['href'], coversrc))
                self.conn.commit()
                selectsql = 'select id,name from movie.movie_hao6v_list WHERE name="%s" order by id desc limit 1' % \
                            item['name']
                cursor.execute(selectsql)
                movie_idinfo = cursor.fetchone()
                print(movie_idinfo)
                # 添加电影的下载链接 这块可以单独封装函数
                add_download_sql = 'insert into movie.movie_hao6v_download_link(movie_id, type_name, type_id,href, text, pwd, create_time, update_time) VALUES '
                templatesql = "(%s,'%s',%s,'%s','%s','%s',%s,%s)"
                insert_sql = ''
                currenttime = int(time.time())
                i = 1
                for download in item['download_a']:
                    download_sql = templatesql % (
                        movie_idinfo['id'], download['type_name'], download['type_id'], download['href'],
                        download['text'], download['pwd'], currenttime,
                        currenttime)
                    if i == 1:
                        insert_sql = download_sql
                    else:
                        insert_sql = insert_sql + ',' + download_sql
                    i = i + 1
                if insert_sql:
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    print(add_download_sql + insert_sql)
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    cursor.execute(add_download_sql + insert_sql)
                    self.conn.commit()
                # 然后添加电影的图片链接 这块可以单独封装函数
                add_img_sql = 'insert into movie.movie_hao6v_imglist(movie_id,movie_name,imgsrc,create_time,update_time) VALUES'
                imgtemplatesql = "(%s,%s,'%s',%s,%s)"
                insert_img_sql = ''
                currenttime = int(time.time())
                i = 1
                for img in imglist:
                    img_sql = imgtemplatesql % (
                        movie_idinfo['id'], item['name'], img, currenttime, currenttime)
                    if i == 1:
                        insert_img_sql = img_sql
                    else:
                        insert_img_sql = insert_img_sql + ',' + img_sql
                    i = i + 1
                if insert_img_sql:
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(add_img_sql + insert_img_sql)
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    cursor.execute(add_img_sql + insert_img_sql)
                    self.conn.commit()
        else:  # 没有取到数据 只报存content 然后手工解析
            currenttime = int(time.time())
            coversrc = ''
            imglist = []
            # 首先从数据库中取出
            for imgsrc in item['imglist']:
                if not coversrc:
                    coversrc = imgsrc
                imglist.append(imgsrc)
            with self.conn.cursor() as cursor:
                sql = "insert into movie.movie_hao6v_list(title, content, region_id, region_name, update_time, create_time, href, coversrc) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(sql, (
                    item['title'], pymysql.escape_string(item['content']), item['region_id'], item['region_name'],
                    currenttime, currenttime, item['href'], coversrc))
                self.conn.commit()
                selectsql = 'select id,title from movie.movie_hao6v_list WHERE title="%s"' % item['title']
                cursor.execute(selectsql)
                movie_idinfo = cursor.fetchone()
                print(movie_idinfo)
                # 添加电影的下载链接 这块可以单独封装函数
                add_download_sql = 'insert into movie.movie_hao6v_download_link(movie_id, type_name, type_id,href, text, pwd, create_time, update_time) VALUES '
                templatesql = "(%s,'%s',%s,'%s','%s','%s',%s,%s)"
                insert_sql = ''
                currenttime = int(time.time())
                i = 1
                for download in item['download_a']:
                    download_sql = templatesql % (
                        movie_idinfo['id'], download['type_name'], download['type_id'], download['href'],
                        download['text'], download['pwd'], currenttime,
                        currenttime)
                    if i == 1:
                        insert_sql = download_sql
                    else:
                        insert_sql = insert_sql + ',' + download_sql
                    i = i + 1
                if insert_sql:
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    print(add_download_sql + insert_sql)
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                    cursor.execute(add_download_sql + insert_sql)
                    self.conn.commit()
                # 然后添加电影的图片链接 这块可以单独封装函数
                add_img_sql = 'insert into movie.movie_hao6v_imglist(movie_id,imgsrc,create_time,update_time) VALUES'
                imgtemplatesql = "(%s,'%s',%s,%s)"
                insert_img_sql = ''
                currenttime = int(time.time())
                i = 1
                for img in imglist:
                    img_sql = imgtemplatesql % (
                        movie_idinfo['id'], img, currenttime, currenttime)
                    if i == 1:
                        insert_img_sql = img_sql
                    else:
                        insert_img_sql = insert_img_sql + ',' + img_sql
                    i = i + 1
                if insert_img_sql:
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(add_img_sql + insert_img_sql)
                    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    cursor.execute(add_img_sql + insert_img_sql)
                    self.conn.commit()


class BtbtMoviescrapyPipeline(object):

    def __init__(self, conn):
        self.conn = conn

    # 从配置文件中读取数据
    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        dbargs = dict(
            host=settings.get('MYSQL_HOST'),
            port=3306,
            user=settings.get('MYSQL_USER'),
            password=settings.get('MYSQL_PASSWD'),
            db=settings.get('MYSQL_DBNAME'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )
        connection = pymysql.connect(**dbargs)
        return cls(connection)

    # {'ages': '2017',
    #  'country': '香港',
    #  'coversrc': 'http://gif-china.cc/uploads/allimg/201710/1d1c9cec07e06924.jpg?h=190',
    #  'download_a': [{'href': None,
    #                  'pwd': '',
    #                  'text': 'HD高清',
    #                  'type_id': 1,
    #                  'type_name': '磁力下载'},
    #                 {'href': 'magnet:?xt=urn:btih:2FF4JF3CHHXEHOI42YSIIPV7YKXXJ42B',
    #                  'pwd': '',
    #                  'text': 'WEB-DL-720P 追龙.Chasing the Dragon.2017.国语中字',
    #                  'type_id': 1,
    #                  'type_name': '磁力下载'},
    #                 {'href': 'magnet:?xt=urn:btih:5JNBGAWDYJMX5XB2TGYXYRW4BRZ3HQXE',
    #                  'pwd': '',
    #                  'text': 'WEB-DL-1080P 追龙.Chasing the Dragon.2017.国语中字',
    #                  'type_id': 1,
    #                  'type_name': '磁力下载'},
    #                 {'href': 'magnet:?xt=urn:btih:095A9D359B69A4CECFD22FE5A0DE158B2D498D96',
    #                  'pwd': '',
    #                  'text': 'TS-720P 追龙.Chasing the Dragon.2017.国语中字[2.63GB]',
    #                  'type_id': 1,
    #                  'type_name': '磁力下载'}],
    #  'href': 'http://www.btbtdy.com/btdy/dy11579.html',
    #  'language': '粤语',
    #  'name': '追龙',
    #  'region_id': 0,
    #  'region_name': '',
    #  'starring': '甄子丹/刘德华/姜皓文/郑则仕/刘浩龙/汤镇业/喻亢/胡然/徐冬冬/黄日华/陈惠敏/周丽淇/吴毅将',
    #  'summary': '\u3000\u3000'
    #             '电影讲述了香港现代史上两大著名狠角色大毒枭跛豪（甄子丹饰）、五亿探长雷洛（刘德华饰）的传奇故事。 \u3000\u3000'
    #             '上世纪六七十年代，香港由英国殖民，权势腐败、社会混乱。1963年，穷困潦倒的青年阿豪（甄子丹饰）偷渡至香港爬上香港毒品霸主之位，一手掌控香港十大黑帮，江湖人称“跛豪”。而雷洛（刘德华饰）则从一位普通探长一步步爬上华人总探长白两手遮天，权势滔天，家财亿万，独霸香港岛……',
    #  'title': '追龙',
    #  'type': ' / 动作/犯罪'}

    # pipeline默认调用
    def process_item(self, item, spider):
        print(item)
        # 正确取到数据
        # 首先取出 封面图片
        currenttime = int(time.time())
        # 首先从数据库中取出
        with self.conn.cursor() as cursor:
            # 需要从数据库中 获取 电影的 类型：然后 匹配下电影的分类
            type_info = []
            # 需要从数据库中 获取 电影的 类型：然后 匹配下电影的分类
            sql = "select id,name from movie.movie_type"
            cursor.execute(sql)
            type_info = cursor.fetchall()
            # type 信息
            movietype_info = re.split('/| ', item['type'])
            type_ids_str = ','
            for movietype in movietype_info:
                # 数据库中爬取的分类
                if not movietype:
                    continue
                type_id = 0
                for typedict in type_info:
                    if typedict['name'] in movietype:
                        type_id = typedict['id']
                        break
                if type_id == 0:
                    # 表示某个字段没有匹配到需要添加到数据库中
                    currenttime = int(time.time())
                    typesql = 'insert into movie_type(`name`,`created_at`) VALUES ("%s","%s")' % (
                        movietype, currenttime)
                    # 分类sql
                    # print('????????????????????????????')
                    # print(typesql)
                    # print('????????????????????????????')
                    cursor.execute(typesql)
                    self.conn.commit()
                    # 然后获取 插入的id 是多少
                    selectsql = 'select id,name from movie.movie_type WHERE name="%s"' % movietype
                    cursor.execute(selectsql)
                    type_id = cursor.fetchone()['id']
                type_ids_str = type_ids_str + str(type_id) + ','
            print('????????????????????????????///////')
            print(type_ids_str)
            print('????????????????????????????///////')
            sql = 'insert into movie_btbtdy_list (name,alias_name,title,ages,country,type,language,starring,' \
                  'summary,content,region_id,region_name,create_time,update_time,href,coversrc) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            print('-------------------------------------------------')
            print(sql)
            print('-------------------------------------------------')
            cursor.execute(sql, (
                item['name'], item['name'], item['name'], item['ages'], item['country'], type_ids_str, item['language'],
                item['starring'], item['summary'], item['content'], item['region_id'], item['region_name'],
                currenttime, currenttime, item['href'], item['coversrc']))
            self.conn.commit()
            selectsql = 'select id,name from movie.movie_btbtdy_list WHERE name="%s" order by id desc limit 1' % \
                        item['name']
            cursor.execute(selectsql)
            movie_idinfo = cursor.fetchone()
            print(movie_idinfo)
            # 添加电影的下载链接 这块可以单独封装函数
            add_download_sql = 'insert into movie.movie_btbtdy_download_link(movie_id, type_name, type_id,href, text, pwd, create_time, update_time) VALUES '
            templatesql = "(%s,'%s',%s,'%s','%s','%s',%s,%s)"
            insert_sql = ''
            currenttime = int(time.time())
            i = 1
            for download in item['download_a']:
                if download['href'] is None:
                    continue
                download_sql = templatesql % (
                    movie_idinfo['id'], download['type_name'], download['type_id'], download['href'],
                    download['text'], download['pwd'], currenttime,
                    currenttime)
                if i == 1:
                    insert_sql = download_sql
                else:
                    insert_sql = insert_sql + ',' + download_sql
                i = i + 1
            if insert_sql:
                print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                print(add_download_sql + insert_sql)
                print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.')
                cursor.execute(add_download_sql + insert_sql)
                self.conn.commit()
