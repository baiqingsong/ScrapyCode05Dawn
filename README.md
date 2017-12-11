# scrapy项目05 淘宝登录

* [准备](#准备)
* [登录页面](#登录页面)
* [提交登录](#提交登录)
* [提取token](#提取token)
* [抓取st](#抓取st)

## 准备
登录中需要首先获取到登录的用户名和加密后的密码还有ua算法后的值  
进入淘宝登录页面，F12调出审查元素，注意需要选中Network,然后选中Preserve log选项，目的为了保留登录时的页面信息  
获取到用户名(TPL_username)，加密的密码(TPL_password_2)和ua(ua)  

## 登录页面
在start_requests调用登录页面的地址和对应的header
```
    login_url = "https://login.taobao.com/member/login.jhtml"
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'Keep-Alive'
        }
    # 抓取登录链接
    def start_requests(self):
        return [Request(self.login_url,
            meta={'cookiejar': 1},
            headers=self.headers,
            callback=self.post_login)]
```
提交信息到post_login方法

## 提交登录
接收登录页面传的信息
```
    login_headers ={
        'Host': 'login.taobao.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0',
        'Referer': 'https://login.taobao.com/member/login.jhtml',
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
    # 提交登录请求
    def post_login(self, response):
        return [FormRequest.from_response(response,
            method='POST',
            meta={'cookiejar' : response.meta['cookiejar']},
            headers=self.login_headers,
            formdata=self.post,
            callback=self.search_token,
            dont_filter=True,
            )]
```
提交登录信息，回调到信息返回处理，提取token

## 提取token
```
    # 登录成功之后 抓取出token
    def search_token(self, response):
        # with open("result.txt", "wb") as f:
        #     f.write(response.body)
        tokenPattern = re.compile('https://passport.alibaba.com/mini_apply_st.js\?site=0&token=(.*?)&')
        tokenMatch = re.search(tokenPattern,response.body)
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
```

## 抓取st
```
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
```