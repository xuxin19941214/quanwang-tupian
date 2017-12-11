from PicTools import PicTools
from lxml import etree
import re
from RedisTools import RedisTool
import pymysql
# 协程并发
import gevent
import time
import logging
from gevent import monkey
# 将一些常见的阻塞，如socket、select等会阻塞的地方实现协程跳转，而不是在那里一直等待，导致整个协程组无法工作。
monkey.patch_all()
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='netall.log',
                    filemode='w')


class PicSpider(object):
    def __init__(self, base_url, site_pattern):
        '''
        :param dic_configs:
        base_url   起始标志， 同时也作为redis缓存的key
        site_pattern  作为站点限制范围
        '''
        self.img_postfix = {'jpg', 'png'}
        self.base_url = base_url
        # 编译一个正则表达式模式，返回一个模式对象
        self.site_pattern = re.compile(site_pattern)
        self.is_empty = False
        self.tool = PicTools()
        self.redis_tool = RedisTool()

    # 从redis缓存中获取一个href并run
    def next_url(self):
        url = self.redis_tool.spop_value(self.tool.convert_url2key(self.base_url))
        if url:
            try:
                self.run(url)
            except Exception as e:
                print(url)
                print(e)
        else:
            self.is_empty = True

    # 循环从redis读取数据
    def start(self):
        self.run(self.base_url)
        while not self.is_empty:
            self.next_url()

    # 图片进数据库
    def save_img(self, base_url, href):
        if self.redis_tool.sismember_value('climbed_img_url', href):
            pass
        else:
            logging.info(href)
            # print('来源：%s' % base_url)
            # print('img地址：%s' % href)
            con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='mysql', database='netall', charset='utf8mb4')
            # 操作游标
            cue = con.cursor()
            print("mysql connect succes")
            try:
                cue.execute("insert into netall1 (base_url,img_url) values(%s,%s)", (base_url, href))
                print("insert success")
            except Exception as e:
                print('Insert error:', e)
                con.rollback()  # 回滚
            else:
                con.commit()  # 提交
            con.close()  # 关闭
            # 加入重复链接。
            self.redis_tool.sadd_value('climbed_img_url', href)

    # 缓存入库操作
    def save_href(self, base_url, href):
        self.redis_tool.sadd_value(self.tool.convert_url2key(base_url), href)

    # 处理href编码问题
    def deal_elementunicode(self, href):
        if isinstance(href, bytes):
            # print('ready convert')
            # print(type(href))
            # href = href.decode()
            return href.decode()
        return href

    # 查询是否重复，抽取href，img入库去重，site_pattern筛选入缓存，插入重复
    def run(self, url):
        climbed = self.redis_tool.sismember_value('climbed_url_%s' % self.tool.convert_url2key(self.base_url), url)
        if climbed:
            return
        html = self.tool.extract_html(url)[0]
        xhtml = etree.HTML(html)
        time.sleep(2)
        hrefs = xhtml.xpath('//a/@href')
        set_hrefs = set(hrefs)
        for href in set_hrefs:
            href = self.deal_elementunicode(href)
            href = self.tool.deal_relative_href(url, href)
            if self.tool.get_postfix(href) in self.img_postfix:
                self.save_img(self.base_url, href)
                # pass
            elif self.site_pattern.search(href):
                self.save_href(self.base_url, href)
        time.sleep(2)
        images = set(xhtml.xpath('//img/@src'))
        for img in images:
            href = self.deal_elementunicode(href)
            img = self.tool.deal_relative_href(url, img)
            self.save_img(self.base_url, img)
        self.redis_tool.sadd_value('climbed_url_%s' % self.tool.convert_url2key(self.base_url), url)

# 列表a中放所有网址和域名
a = [['http://www.58pic.com/', '58pic']]

# a = [['https://aiji66.com/', 'aiji66']]

spawn_list = []
for i, j in a:
    spider = PicSpider(i, j)
    spawn_list.append(gevent.spawn(spider.start))
gevent.joinall(spawn_list)
