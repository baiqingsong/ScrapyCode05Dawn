# -*- coding: utf-8 -*-
import re
import logging

from scrapy import Spider, Request, FormRequest

from ScrapyCode05Dawn.items import TaobaoOrderItem

logger = logging.getLogger(__name__)


class TaobaoOrderSpider(Spider):

    login_url = "https://login.taobao.com/member/login.jhtml"
    order_items_url = "https://buyertrade.taobao.com/trade/itemlist/asyncBought.htm?action=itemlist/BoughtQueryAction&event_submit_do_query=1&_input_charset=utf8"
    crawl_url = 'https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm'
    login_headers ={
        'Host': 'login.taobao.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0',
        'Referer': 'https://login.taobao.com/member/login.jhtml',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'Keep-Alive'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'Keep-Alive'
    }
    username = ''  # taobao user name
    ua = ''  # ua_code
    password2 = ''   # password2
    post = {
        'TPL_username': username,
        'TPL_password': '',
        'ncoSig': '',
        'ncoSessionid': '',
        'ncoToken': '73743bd7087e562773a6798e0be429c41aa9129e',
        'slideCodeShow': 'false',
        'lang': 'zh_CN',
        'loginsite': '0',
        'newlogin': '0',
        'TPL_redirect_url': '',
        'from': 'tb',
        'fc': 'default',
        'style': 'default',
        'css_style': '',
        'keyLogin': 'false',
        'qrLogin': 'true',
        'newMini': 'false',
        'newMini2': 'false',
        'tid': '',
        'loginType': '3',
        'minititle': '',
        'minipara': '',
        'pstrong': '',
        'sign': '',
        'need_sign': '',
        'isIgnore': '',
        'full_redirect': '',
        'sub_jump': '',
        'popid': '',
        'callback': '',
        'guf': '',
        'not_duplite_str': '',
        'need_user_id': '',
        'poy': '',
        'gvfdcname': '10',
        'gvfdcre': '',
        'from_encoding': '',
        'sub': '',
        'TPL_password_2': password2,
        'loginASR': '1',
        'loginASRSuc': '1',
        'allp': '',
        'oslanguage': 'zh-CN',
        'sr': '1536*864',
        'osVer': '',
        'naviVer': 'firefox|48',
        'miserHardInfo': '',
        'ua': ua,
        'um_token': 'HV01PAAZ0ab2a16965ccf77857b3ffe0000d7439'
    }
    name = "taobao"
    download_delay = 5
    allowed_domains = ["taobao.com", "passport.alibaba.com"]

    # 抓取登录链接
    def start_requests(self):
        return [Request(self.login_url,
            meta={'cookiejar': 1},
            headers=self.headers,
            callback=self.post_login)]

    # 提交登录请求
    def post_login(self, response):
        return [FormRequest.from_response(response,
            method='POST',
            meta={'cookiejar': response.meta['cookiejar']},
            headers=self.login_headers,
            formdata=self.post,
            callback=self.search_token,
            dont_filter=True,
            )]

    # 登录成功之后 抓取出token
    def search_token(self, response):
        # with open("result.txt", "wb") as f:
        #     f.write(response.body)
        tokenPattern = re.compile('https://passport.alibaba.com/mini_apply_st.js\?site=0&token=(.*?)&')
        tokenMatch = re.search(tokenPattern, response.body)
        if tokenMatch:
            logger.log(1, "token found")
            token = tokenMatch.group(1)
            tokenURL = 'https://passport.alibaba.com/mini_apply_st.js?site=0&token=%s&callback=stCallback6' % token

            return [Request(tokenURL,
                meta={'cookiejar': response.meta['cookiejar']},
                headers=self.headers,
                callback=self.search_st,
                )]
        else:
            logger.warning("login failed[on search_token]")

    # 抓取出st code
    def search_st(self, response):
        pattern = re.compile('{"st":"(.*?)"}', re.S)
        result = re.search(pattern, response.body)
        if result:
            logger.log(1, "st code found")
            st = result.group(1)
            stURL = 'https://login.taobao.com/member/vst.htm?st=%s&TPL_username=%s' % (st, self.username)
            return [Request(stURL,
                method="GET",
                headers=self.headers,
                meta={'cookiejar': response.meta['cookiejar']},
                callback=self.login_process,
                )]
        else:
            logger.warning("login failed[on search_st]")

    # 用st code 进行登录
    def login_process(self, response):
        pattern = re.compile('top.location.href = "(.*?)"', re.S)
        match = re.search(pattern, response.body)
        if match:
            logger.log(1, "st code found")
            return [Request(
                self.crawl_url,
                method='GET',
                meta={'cookiejar': response.meta['cookiejar']},
                headers=self.headers,
                dont_filter=True,
                callback=self.start_crawl,
            )]
        else:
            logger.warning("login failed[on search_st]")

    # 开始爬取订单列表
    def start_crawl(self, response):
        # with open("result.txt", "wb") as f:
        #     f.write(response.body)
        # find next page
        # from first pages to start
        pattern = re.compile('"totalPage":(.*?)},', re.S)
        match = re.search(pattern, response.body)
        if match:
            totalPage = int(match.group(1))  # get total page
            if totalPage > 0:
                pageNum = 0
                while pageNum <= totalPage:
                    pageNum += 1
                    yield FormRequest(
                        self.order_items_url,
                        method="POST",
                        headers=self.headers,
                        formdata={
                            'pageNum': str(pageNum),
                            'pageSize': '15',
                            'action': 'itemlist/BoughtQueryAction',
                            'prePageNo': '1',
                            'buyerNick': '',
                            'dateBegin': '0',
                            'dateEnd': '0',
                            'lastStartRow': '',
                            'logisticsService': '',
                            'options': '0',
                            'orderStatus': '',
                            'queryBizType': '',
                            'queryOrder': 'desc',
                            'rateStatus': '',
                            'refund': '',
                            'sellerNick': '',
                            },
                        callback=self.parse_item,
                        meta={'cookiejar': response.meta['cookiejar']}
                        )

    def parse_item(self, response):
        item = TaobaoOrderItem()
        item["order_json"] = response.body_as_unicode()
        return item
