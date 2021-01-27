#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# @AUTHOR: Rabbir
# @FILE: /root/Github/steampy/steampy/login.py
# @DATE: 2021/01/27 Wed
# @TIME: 15:05:26
#
# @DESCRIPTION: Login 类和方法


import rsa
import time
import base64
import requests
from steampy import guard
from steampy.models import SteamUrl
from steampy.exceptions import InvalidCredentials, CaptchaRequired


"""
@description: Steam 登录执行类
-------
@param:
-------
@return:
"""
class LoginExecutor:

    """
    @description: 初始化
    -------
    @param:
    -------
    @return:
    """
    def __init__(self,
                 username: str,
                 password: str,
                 shared_secret: str,
                 session: requests.Session) -> None:
        self.username = username
        self.password = password
        # 默认不填写令牌码，等到登录后返回需要则取令牌取再试登录
        self.one_time_code = ''
        self.shared_secret = shared_secret
        self.session = session

    """
    @description: 登录方法
    -------
    @param:
    -------
    @return:
    """
    def login(self) -> requests.Session:
        login_response = self._send_login_request()
        # 邮箱验证直接报错？
        self._check_for_captcha(login_response)
        # 需要手机令牌就自动获取后再次登录
        login_response = self._enter_steam_guard_if_necessary(login_response)
        # 验证登录状态
        self._assert_valid_credentials(login_response)
        self._perform_redirects(login_response.json())
        self.set_sessionid_cookies()
        # 返回登录成功的会话 Session
        return self.session

    """
    @description: 发送登录请求
    -------
    @param:
    -------
    @return:
    """
    def _send_login_request(self) -> requests.Response:
        # 获取 RSA 公钥
        rsa_params = self._fetch_rsa_params()
        # 加密 Steam 密码
        encrypted_password = self._encrypt_password(rsa_params)
        # 获取服务器端生成 RSA 公钥的时间戳
        rsa_timestamp = rsa_params['rsa_timestamp']
        # 生成 Steam 登录所需的参数
        request_data = self._prepare_login_request_data(encrypted_password,
                                                        rsa_timestamp)
        # 登录并返回 Response
        return self.session.post(SteamUrl.STORE_URL+'/login/dologin',
                                 data=request_data)

    """
    @description: 获取 Steam 社区和 Steam 商店回话的 Session ID 和 Url
    -------
    @param:
    -------
    @return:
    """
    def set_sessionid_cookies(self):
        sessionid = self.session.cookies.get_dict()['sessionid']
        community_domain = SteamUrl.COMMUNITY_URL[8:]
        store_domain = SteamUrl.STORE_URL[8:]
        # Steam 社区会话的 Session ID 和 Url
        community_cookie = self._create_session_id_cookie(sessionid,
                                                          community_domain)
        # Steam 商店会话的 Session ID 和 Url
        store_cookie = self._create_session_id_cookie(sessionid,store_domain)
        self.session.cookies.set(**community_cookie)
        self.session.cookies.set(**store_cookie)

    """
    @description: 拼接会话 Session 的信息
    -------
    @param:
    -------
    @return:
    """
    @staticmethod
    def _create_session_id_cookie(sessionid: str, domain: str) -> dict:
        return {"name": "sessionid",
                "value": sessionid,
                "domain": domain}

    """
    @description: 获得 RSA-KEY
    -------
    @param:
    -------
    @return:
    """
    def _fetch_rsa_params(self, current_number_of_repetitions: int = 0) -> dict:
        maximal_number_of_repetitions = 5
        key_response = self.session.post(SteamUrl.STORE_URL \
                                            + '/login/getrsakey/',
                                         data={'username': self.username})
        key_response = key_response.json()
        try:
            rsa_mod = int(key_response['publickey_mod'], 16)
            rsa_exp = int(key_response['publickey_exp'], 16)
            rsa_timestamp = key_response['timestamp']
            return {'rsa_key': rsa.PublicKey(rsa_mod, rsa_exp),
                    'rsa_timestamp': rsa_timestamp}
        except KeyError:
            if current_number_of_repetitions < maximal_number_of_repetitions:
                return self._fetch_rsa_params(current_number_of_repetitions + 1)
            else:
                raise ValueError('没有获取到 RSA-KEY')

    """
    @description: 加密密码（先转为 UTF-8 编码，再 RSA 加密，最后 BASE64 加密）
    -------
    @param:
    -------
    @return:
    """
    def _encrypt_password(self, rsa_params: dict) -> str:
        return base64.b64encode(rsa.encrypt(self.password.encode('utf-8'),
                                            rsa_params['rsa_key']))

    """
    @description: 准备登录所需的信息
    -------
    @param:
    -------
    @return:
    """
    def _prepare_login_request_data(self,
                                    encrypted_password: str,
                                    rsa_timestamp: str) -> dict:
        return {
            'password': encrypted_password,
            'username': self.username,
            'twofactorcode': self.one_time_code,
            'emailauth': '',
            'loginfriendlyname': '',
            'captchagid': '-1',
            'captcha_text': '',
            'emailsteamid': '',
            'rsatimestamp': rsa_timestamp,
            'remember_login': 'true',
            'donotcache': str(int(time.time()*1000))
        }

    """
    @description: 判断登录后是否需要验证码
    -------
    @param:
    -------
    @return:
    """
    @staticmethod
    def _check_for_captcha(login_response: requests.Response) -> None:
        if login_response.json().get('captcha_needed', False):
            raise CaptchaRequired('Steam 登录需要验证码')

    """
    @description: 登录如果需要二步验证码的话自动填入
    -------
    @param:
    -------
    @return:
    """
    def _enter_steam_guard_if_necessary(self,
            login_response: requests.Response) -> requests.Response:
        if login_response.json()['requires_twofactor']:
            # 获取令牌码
            self.one_time_code = guard.generate_one_time_code(
                self.shared_secret)
            # 再执行一次从获取 RSA 公钥和时间开始的登录
            return self._send_login_request()
        return login_response

    """
    @description: 登录失败则报错
    -------
    @param:
    -------
    @return:
    """
    @staticmethod
    def _assert_valid_credentials(login_response: requests.Response) -> None:
        if not login_response.json()['success']:
            raise InvalidCredentials(login_response.json()['message'])

    """
    @description: 登录后的验证操作？
    -------
    @param:
    -------
    @return:
    """
    def _perform_redirects(self, response_dict: dict) -> None:
        parameters = response_dict.get('transfer_parameters')
        if parameters is None:
            raise Exception('Cannot perform redirects after login,' \
                            + ' no parameters fetched')
        for url in response_dict['transfer_urls']:
            self.session.post(url, parameters)

    """
    @description: 返回个人主页
    -------
    @param:
    -------
    @return:
    """
    def _fetch_home_page(self, session: requests.Session) -> requests.Response:
        return session.post(SteamUrl.COMMUNITY_URL + '/my/home/')


"""
@description: 单体测试
-------
@param:
-------
@return:
"""
if __name__ == "__main__":
    print("todo...")