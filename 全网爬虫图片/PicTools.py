from lxml import etree
import requests
import re


class PicTools(object):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        }
        # 匹配任何不可见字符，包括空格、制表符、换页符等等
        self.pattern_space = re.compile('\s')

    # 将url转为redis的key（将：转为@）
    def convert_url2key(self, url):
        return url.replace(':', '@@@')

    # 取后缀，判断是不是图片，取最后一个点后面就是后缀，lower将字符串全变成小写
    def get_postfix(self, url):
        start = url.rfind('.') + 1
        if start:
            return url[start:].lower()
        return ''

    def extract_html(self, url):
        '''
        ①解决编码问题， 通过try  exception  获取html源码。
        ②加入Requests Headers
        :param url:
        :return: [html, after_url]
        '''
        # isinstance判断变量是否是str这个类型
        if not isinstance(url, str):
            url = url.decode()
        ori = requests.get(url, headers=self.headers)
        b_html = ori.content
        after_url = ori.url
        try:
            html = b_html.decode(encoding='utf-8')
        except:
            try:
                html = b_html.decode(encoding='gbk')
            except:
                html = ori.text
        return [html, after_url]

    # 取域名，http：//占7个字符，https：//占8个字符
    def get_hosts(self, url):
        try:
            end = url.index('/', 8)
            # 返回域名
            return url[:end]
        except:
            return url

    # 将一个href转换成绝对链接,startswith判断是否以指定字符串开头,有些href是javascript脚本代码或#之类的链接
    def deal_relative_href(self, front_href, h):
        if isinstance(front_href, bytes):
            front_href = front_href.decode()
        exit_set = ('#', '', '/')
        if h.startswith('java') or (h in exit_set):
            return front_href
        is_https = h.startswith('https')

        if h.startswith('//'):
            if is_https:
                # h = 'https:' + h
                # print(h)
                # return h
                return 'https:' + h
            else:
                # h = 'http:' + h
                # print(h)
                # return h
                return 'http:' + h
            # return 'http:' + h
        if self.pattern_space.search(h):
            return front_href
        if not h.startswith('http'):
            return front_href + h
        else:
            return h
