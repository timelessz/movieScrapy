import base64
import urllib
from math import ceil

import pymysql
import re
import scrapy
import time
from scrapy.selector import Selector
# 读取配置文件相关
from scrapy.utils.project import get_project_settings
from movieScrapy.items import XunleipuMovieItem

'''
思路：
该网站爬取迅雷铺中的内容然后解析到数据库中：
应该保存到数据库

1、原文链接。
2、原文中图片的链接 。
3、原文全部内容 包含图片的链接。

'''


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

    def reconn(self):
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
            'dalu': {
                'url': 'http://www.xlpu.cc/category/4_%s.htm',
                'start_url': 'http://www.xlpu.cc/category/4_1.htm',
                'id': 4,
                'name': '大陆电影'
            },
            'rihan': {
                'url': 'http://www.xlpu.cc/category/2_%s.htm',
                'start_url': 'http://www.xlpu.cc/category/2_1.htm',
                'id': 2,
                'name': '日韩电影'
            },
            'gangtai': {
                'url': 'http://www.xlpu.cc/category/3_%s.htm',
                'start_url': 'http://www.xlpu.cc/category/3_1.htm',
                'id': 3,
                'name': '港台电影'
            },
            'classics': {
                'url': 'http://www.xlpu.cc/category/11_%s.htm',
                'start_url': 'http://www.xlpu.cc/category/11_1.htm',
                'id': 5,
                'name': '经典电影'
            },
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

    def test(self):
        text = '''
                <DIV id=classpage6>
                <!--Content Start-->
                <div style="float:left;overflow:hidden;padding-bottom:15px;">
                <IMG border=0 src="http://pic.66vod.net:888/tupian/2014/01984.jpg"><BR><BR>◎译　　名　佐罗传奇/黑侠梭罗Z传奇 <BR>◎片　　名　The&nbsp;Legend&nbsp;of&nbsp;Zorro <BR>◎年　　代　2005 <BR>◎国　　家　美国 <BR>◎类　　别　动作/冒险/西部 <BR>◎语　　言　英语 <BR>◎字　　幕　中英双字 <BR>◎IMDB评分&nbsp;5.7/10&nbsp;&nbsp;15,070&nbsp;votes <BR>◎文件格式　BD-RMVB <BR>◎视频尺寸　1024&nbsp;x&nbsp;576 <BR>◎文件大小　1CD <BR>◎片　　长　130MiN <BR>◎导　　演　马丁·坎贝尔&nbsp;Martin&nbsp;Campbell <BR>◎主　　演　安东尼奥·班德拉斯&nbsp;Antonio&nbsp;Banderas&nbsp;&nbsp;....&nbsp;&nbsp;Zorro/Alejandro&nbsp; <BR>　　　　　　迈克尔·埃默森&nbsp;Michael&nbsp;Emerson&nbsp;&nbsp;....&nbsp;&nbsp;Harrigan&nbsp; <BR>　　　　　　舒尔·亨斯利&nbsp;Shuler&nbsp;Hensley&nbsp;&nbsp;....&nbsp;&nbsp;Pike&nbsp; <BR>　　　　　　小佩得罗·阿蒙达里兹&nbsp;Pedro&nbsp;Armendáriz&nbsp;Jr.&nbsp;&nbsp;....&nbsp;&nbsp;Governor&nbsp;Riley&nbsp;(as&nbsp;Pedro&nbsp;Armendariz)&nbsp; <BR>　　　　　　玛丽·克罗斯比&nbsp;Mary&nbsp;Crosby&nbsp;&nbsp;....&nbsp;&nbsp;Governor’s&nbsp;Wife&nbsp; <BR>　　　　　　凯瑟琳·泽塔-琼斯&nbsp;Catherine&nbsp;Zeta-Jones&nbsp;&nbsp;....&nbsp;&nbsp;Elena&nbsp; <BR>　　　　　　Mauricio&nbsp;Bonet&nbsp;&nbsp;....&nbsp;&nbsp;Don&nbsp;Verdugo&nbsp; <BR>　　　　　　Fernando&nbsp;Becerril&nbsp;&nbsp;....&nbsp;&nbsp;Don&nbsp;Diaz&nbsp; <BR>　　　　　　Xavier&nbsp;Marc&nbsp;&nbsp;....&nbsp;&nbsp;Don&nbsp;Robau&nbsp; <BR>　　　　　　Pepe&nbsp;Olivares&nbsp;&nbsp;....&nbsp;&nbsp;Phineas&nbsp;Gendler&nbsp; <BR>　　　　　　Alexa&nbsp;Benedetti&nbsp;&nbsp;....&nbsp;&nbsp;Lupe&nbsp; <BR>　　　　　　Tony&nbsp;Amendola&nbsp;&nbsp;....&nbsp;&nbsp;Father&nbsp;Quintero&nbsp; <BR>　　　　　　Brandon&nbsp;Wood&nbsp;&nbsp;....&nbsp;&nbsp;Ricardo&nbsp; <BR>　　　　　　Alberto&nbsp;Reyes&nbsp;&nbsp;....&nbsp;&nbsp;Brother&nbsp;Ignacio&nbsp; <BR>　　　　　　Julio&nbsp;Oscar&nbsp;Mechoso&nbsp;&nbsp;....&nbsp;&nbsp;Frey&nbsp;Felipe&nbsp; <BR>　　　　　　Gustavo&nbsp;Sanchez-Parra&nbsp;&nbsp;....&nbsp;&nbsp;Cortez&nbsp;(as&nbsp;Gustavo&nbsp;Sánchez&nbsp;Parra)&nbsp; <BR>　　　　　　阿德里安·阿隆索&nbsp;Adrian&nbsp;Alonso&nbsp;&nbsp;....&nbsp;&nbsp;Joaquin&nbsp; <BR>　　　　　　尼克·齐兰德&nbsp;Nick&nbsp;Chinlund&nbsp;&nbsp;....&nbsp;&nbsp;Jacob&nbsp;McGivens&nbsp; <BR>　　　　　　Giovanna&nbsp;Zacarías&nbsp;&nbsp;....&nbsp;&nbsp;Blanca&nbsp;(as&nbsp;Giovanna&nbsp;Zacarias)&nbsp; <BR>　　　　　　Carlos&nbsp;Cobos&nbsp;&nbsp;....&nbsp;&nbsp;Tabulador&nbsp; <BR><BR>◎简　　介　 <BR><BR>&nbsp;&nbsp;&nbsp;&nbsp;1850年加州即将成为美利坚合众国第三十一州，但是某些别有用心的人士以及一个中古时代的神秘组织却为了本身的利益从中阻挠，于是蒙面侠佐罗必须再度出马，帮助加州人民对抗这些强权恶霸。在这同时，贪污腐败的麦吉文伯爵不断欺压善良的老百姓，强占他们的土地，并威胁他们的人身安全。蒙面侠佐罗也必须阻止他的恶行。&nbsp; <BR><BR>　　从上一代的蒙面侠佐罗手中接棒的亚利桑德罗现在已经和伊莲娜结婚，并有一个十岁大的儿子瓦金。瓦金非常想念他那经常不在家的爸爸，但是当他爸爸回家，他又很希望他爸爸跟他心目中的大英雄蒙面侠佐罗一样英勇威武，而他完全不知道他爸爸和蒙面侠佐罗竟然是同一个人。&nbsp; <BR><BR>　　经过多年冒险犯难的危险生活，伊莲娜希望亚利桑德罗在成为蒙面侠佐罗以及当个好家庭主夫之间做出选择，他也答应她退隐江湖，不再过问世事。但是当危机发生，亚利桑德罗不得不再度戴上面罩拯救世人，伊莲娜觉得被他欺骗，于是把他赶出家门，而且很快就向他提出离婚要求。&nbsp; <BR><BR>　　这时伊莲娜的昔日同窗好友法国贵族亚曼搬来加州开设酒厂，他很高兴得知伊莲娜已和丈夫分居，于是立即对她展开热烈追求，在这同时他也是古老兄弟会亚拉冈骑士团的会长。&nbsp;蒙面侠佐罗亚利桑德罗在内忧外患的夹击之下，必须想办法击败敌人解救受难的加州人民，同时还要权利担负起身为丈夫及父亲的责任。&nbsp; <BR><BR>幕后制作 <BR><BR>　　【延续传奇】&nbsp; <BR><BR>　　佐罗问世于约翰斯顿·麦考利(Johnston&nbsp;McCulley)在1919年创作的小说《The&nbsp;Curse&nbsp;Of&nbsp;Capistrano》，佐罗被认为是美国现代小说中的第一个蒙面英雄。《佐罗传奇》的导演马丁·坎贝尔说：“佐罗保护的是普通人，与在他之前的一些英雄有所不同，他是真正的人民英雄。他没有特殊的能力和武器，只有长剑、马鞭和智慧。值得一提的是，佐罗虽然身手不凡，但的确是个有血有肉的男人，与当今盛行的超级英雄的数字形象大相径庭。”制片人劳里·麦克唐纳(Laurie&nbsp;MacDonald)说：“我之所以喜欢佐罗，并认为我们都会产生共鸣是因为因为他没有超人的能力。他是个普通男人，当然，他的马术和剑术非常出色，但在本质上，他和其他人一样都要面对常人的烦恼。”&nbsp;年前，《佐罗的面具》取得了巨大成功，在全球院线狂赚2亿5000万美元。作为续集，《佐罗传奇》的故事发生在10年后，佐罗和埃琳娜结婚成家，育有一子。“新冒险的挑战之一在于上部影片结尾，佐罗和埃琳娜结婚了，”麦克唐纳说，“可是在10年后，两人的婚姻出现了一些严重的问题，从而导致了婚姻关系的破裂。爱情故事总是在非常情况下才会分外动人，在本片故事中，两位恋人将冲破重重障碍才能破镜重圆。”制片人沃尔特·F·帕克斯(Walter&nbsp;F。　Parkes)说：“影片故事回归为好莱坞的古典喜剧，即男女主人公无法忍受对方，却又无法失去对方。这不仅是潜在的叙事设计，还将重新点燃两人的爱火。”&nbsp; <BR><BR>　　安东尼奥·班德拉斯在阅读剧本时，很快发现其中具备了首部电影的所有元素，他说：“喜剧风格、精彩的对白和紧张的冒险对这种电影很重要，当我得知包括马丁在内的很多原班人马将重聚一堂时，顿时感到格外兴奋。”&nbsp; <BR><BR>　　凯瑟琳·泽塔-琼斯说：“如果没有《佐罗的面具》的相同魅力，我们谁也不愿开始这新的旅程。当我们发现新的剧本一脉相承，我们知道精彩即将延续。”&nbsp; <BR><BR>　　【关于拍摄】&nbsp; <BR><BR>　　众所周知，坎贝尔是一位技艺娴熟的动作片导演，他承认，本片是在他的作品中动作戏最复杂的一个。他说：“在击剑方面，本片比上部要更复杂。在临近影片结尾时，有段在火车上打斗的高潮戏。因为动作场景繁多，所以摄制组和特技组必须周密计划，并使用了情节串连图板。”&nbsp; <BR><BR>　　与坎贝尔合作多年的摄影指导菲尔·莫修(Phil&nbsp;Meheux)说：“马丁对动作场面可谓驾轻就熟，他知道如何去拍摄，这得宜于他在早年拍摄的警匪电视剧。不但拍摄非常迅速，而且计划非常周密，马丁非常善于计划。”&nbsp; <BR><BR>　　本片的剑术指导是《佐罗的面具》中的剑术指导助理马克·艾维(Mark&nbsp;Ivie)，他说：“本片中的击剑比上部更进一步，更好看更复杂，击剑的地点也相当多变，比如在导水管上、在葡萄酒厂里和在开动火车的车顶。马丁是个出色的动作片导演，他将动作体现到情节串连图板上，于是我们可以一起进行讨论。”&nbsp;特技协调人加里·鲍威尔(Gary&nbsp;Powell)在担纲本片之前，刚刚参与《亚历山大大帝》的拍摄。当他拿到影片的拍摄计划，发现《佐罗传奇》是他指导过的最繁忙的影片之一，因为每天都要拍摄特技动作，每个人都有很多事要忙。泽塔·琼斯说：“我想，在《佐罗的面具》中鲍勃·安德森(Bob&nbsp;Anderson)和马克·艾维对我的训练在这部影片中起到了重要作用，如果没有他们精湛的传授，在续集中我不可能这么快就恢复，动作也不可能如此流畅。我应该将剑术当作我的业余爱好。”班德拉斯在片中有很多特技动作，他要求尽可能的亲自完成。他说：“我喜欢诚实的对待观众，我希望他们能在片中看到我的努力。”事实证明，班德拉斯是个出色的剑客，他的身手要强于一些特技演员。虽然影片故事发生在加州，但由于在加州无法呈现出19世纪风貌，所以剧组选择了墨西哥的圣路易斯波托西(San&nbsp;Luis&nbsp;Potosí)。当地被认为是墨西哥殖民地的中心地带，在西班牙统治时期，当地盛产谷物和白银。圣路易斯波托西为半沙漠地形，于是恶劣的天气给剧组造成了诸多不便。特别是在拍摄阿蒙德的淘宝网狂欢节时，班德拉斯、泽塔-琼斯和500名临时演员一同起舞，突然间电闪雷鸣，转瞬间演职人员都成了落汤鸡，站在一英尺半的水中。在拍摄这场戏的一周里，剧组上下一直同大雨进行着斗争，每当准备开机，总会有雷电划破长空，倾盆大雨随即而至。鲜花被打蔫，蜡烛被打灭，剧组人员急忙挽救烟火器材。这些艰辛是在影片的画面中看不到的。&nbsp; <BR><BR>　　在拍摄《佐罗的面具》时，剧组曾多次转换拍摄地，由此浪费了大量时间，所以这次导演决定在一个地方拍摄。最终，坎贝尔决定将哥哥朗庄园作为中心景区，影片75%的场景都是在此拍摄完成。&nbsp; <BR><BR>　　哥哥朗庄园由名为哥哥朗的西班牙人在1750年建造，他在圣路易斯波托西开设了银矿，从而不断聚敛财富，整个庄园最大时曾占地35000公顷。由于当地自然灌溉便利，所以哥哥朗庄园以淘宝农业高产著称。19世纪末期，家族将重心转移到纺织和制酒上，并建起了多家工厂。哥哥朗庄园现在的主人非常愿意协助《佐罗传奇》的拍摄，他的重建成果由此得以呈现在大银幕上。 <BR><BR><IMG border=0 src="http://pic.66vod.net:888/tupian/2014/01977.jpg" width=650><BR><BR>下载地址：<BR><BR><A href="ftp://dy131.com:6vdy.com@ftp1.66e.cc:2624/【6v电影www.6vdy.com】佐罗传奇.BD国英音轨中英双字1024高清.mkv" target=_blank>佐罗传奇.BD国英音轨中英双字1024高清.mkv</A><BR><BR><A href="ftp://dy131.com:6vdy.com@ftp1.66e.cc:2624/【6v电影www.6vdy.com】佐罗传奇DVD.mp4" target=_blank>佐罗传奇DVD.mp4</A><BR><BR><A href="ftp://6:6@ftp2.kan66.com:4165/【6v电影www.dy131.com】佐罗传奇BD中英双字1024高清.rmvb" target=_blank>佐罗传奇BD中英双字1024高清.rmvb</A><BR>
                </div>
                <br>
                <div>
                <script src='/js/thundergvod.js'></script>
                <script src='http://pstatic.xunlei.com/js/webThunderDetect.js'></script>
                <script src='http://pstatic.xunlei.com/js/base64.js'></script>
                <script src='http://pstatic.xunlei.com/js/thunderForumLinker.js'></script>
                <script language="javascript">
                    var thunderPid="16214";
                      var thunderExceptPath="play.html";
                    thunderFuncType=false;
                    thunderLinker();
                </script>
                </div>
                <script language=javascript src="../adv/ad_5.js"></script>
                <div class="lz_info_div"><ul>
                <script language=javascript src="../adv/ad_12.js"></script>
                </ul>
                </div>
                </DIV>
                '''
        # download_link_a = Selector(text=content_sel.extract()).xpath('//a')
        download_link_a = Selector(text=text.lower()).xpath('//a')
        a_download_info = []
        for a in download_link_a:
            href = a.xpath('@href').extract_first()
            text = a.xpath('text()').extract_first()
            download_info = self.analyse_doanload_linkinfo(href)
            # 百度云链接的话需要密码  这种情况下需要自己进行操作 获取密码
            a_download_info.append({'href': href, 'pwd': '', 'text': text, 'type_id': download_info['type_id'],
                                    'type_name': download_info['type_name']})
        print(a_download_info)
        return

    def analyse_doanload_linkinfo(self, href):
        type_id = 10
        type_name = '其他'
        if 'magnet:' in href:
            type_id = 1
            type_name = '磁力下载'
        elif 'ed2k://' in href:
            type_id = 2
            type_name = '电驴下载'
        elif 'ftp://' in href:
            type_id = 3
            type_name = '迅雷下载'
        elif 'pan' in href:
            type_id = 4
            type_name = '百度云'
        elif 'torrent' in href:
            type_id = 5
            type_name = '种子'
        return {'type_id': type_id, 'type_name': type_name}

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
            i = i + 1
            if self.get_movie(item['title']) is None:
                item['addtime'] = tr.xpath('string(td[2])').extract_first()
                item['region_id'] = category['id']
                item['region_name'] = category['name']
                parent_url = category['url']
                # 获取详细内容页面 的url 使用相对路径跟绝对路径
                relative_href = tr.xpath('td[1]/a/@href').extract_first()
                if relative_href:
                    # 把相对路径转换为绝对路径
                    href = urllib.parse.urljoin(parent_url, relative_href)
                    # href = self.base_url + relative_href
                    item['href'] = href
                    request = scrapy.Request(url=href, callback=self.parse_content)
                    request.meta['item'] = item
                    print(href)
                    yield request
            else:
                time.sleep(1)
                print('**********************************')
                print(item['title'] + '电影已经存在，放弃爬取数据')
                print('**********************************')
        category = response.meta['category']
        start_url = category['url']
        # for i in range(2,page_num+1)
        for i in range(2, 5):
            url = start_url % i
            print(url)
            request = scrapy.Request(url=url, callback=self.parse_list)
            request.meta['category'] = category
            yield request

    def get_movie(self, title):
        self.reconn()
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM movie_xunleipu_list where title like '%" + title + "%'")
        movie= cur.fetchone()
        self.conn.close()
        return movie

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
            # 首先需要查询下是不是已经有重复 重复的跳出
            i = i + 1
            if self.get_movie(item['title']) is None:
                item['addtime'] = tr.xpath('string(td[2])').extract_first()
                item['region_id'] = category['id']
                item['region_name'] = category['name']
                parent_url = category['url']
                # 获取详细内容页面 的url 使用相对路径跟绝对路径
                relative_href = tr.xpath('td[1]/a/@href').extract_first()
                if relative_href:
                    href = urllib.parse.urljoin(parent_url, relative_href)
                    # href = self.base_url + relative_href
                    item['href'] = href
                    request = scrapy.Request(url=href, callback=self.parse_content)
                    request.meta['item'] = item
                    print(href)
                    yield request
            else:
                time.sleep(1)
                print('**********************************')
                print(item['title'] + '电影已经存在，放弃爬取数据')
                print('**********************************')

    def parse_content(self, response):
        '''
        解析页面的内容
        '''
        item = response.meta['item']
        sel = Selector(response)
        # 这个地方要修改 为
        content_selector = sel.xpath('//*[@id="classpage2"]/div')
        content_sel = None
        for content in content_selector:
            content_info = content.extract()
            if ('片' in content_info and '名' in content_info) or ('简' in content_info and '介' in content_info):
                content_sel = content
                break
        html_text = content_sel.extract()
        download_link_a = Selector(text=html_text.lower()).xpath('//a')
        a_download_info = []
        for a in download_link_a:
            href = a.xpath('@href').extract_first()
            text = a.xpath('text()').extract_first()
            download_info = self.analyse_doanload_linkinfo(href)
            # 百度云链接的话需要密码  这种情况下需要自己进行操作 获取密码
            a_download_info.append({'href': href, 'pwd': '', 'text': text, 'type_id': download_info['type_id'],
                                    'type_name': download_info['type_name']})
        if not a_download_info:
            print(content_sel.extract())
            print(
                '/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////没有获取到电影下载链接///////////////////////////////////')
            return
        item['download_a'] = a_download_info
        # 提取处内容来
        if content_sel:
            content = content_sel.extract()
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
        if len(content_list) < 2:
            return item
        for content_field in content_list:
            # 清除\r\n
            content_field = content_field.strip(' \t\n\r')
            if not content_field:
                continue
            for field in all_field:
                if '简介' == field['text']:
                    if '简' in content_field and '介' in content_field:
                        content_field = self.replace_str(content_field, a_download_info)
                        fieldtext = content_field.replace(field['text'], '')
                        item[field['field']] = fieldtext.strip(' \t\n\r')
                elif field['text'] in content_field and content_field.find(field['text']) == 0:
                    fieldtext = content_field.replace(field['text'], '')
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
