#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# @AUTHOR: Rabbir
# @FILE: /root/Github/steampy/steampy/chat.py
# @DATE: 2021/01/27 Wed
# @TIME: 16:00:58
#
# @DESCRIPTION: Steam Chat 类和方法


import bs4
import re
from steampy.models import Endpoints, SteamUrl
from steampy.utils import account_id_to_steam_id


"""
@description: Steam Chat 类
-------
@param:
-------
@return:
"""
class SteamChat():

    """
    @description: 初始化
    -------
    @param:
    -------
    @return:
    """
    def __init__(self, session):
        self._session = session
        self._chat_params = {}

    """
    @description: 获取会话 Token
    -------
    @param:
    -------
    @return:
    """
    def _get_access_token(self):
        response = self._session.get(SteamUrl.COMMUNITY_URL+"/chat")
        response.raise_for_status()
        response_soup = bs4.BeautifulSoup(response.text, "html.parser")
        print(response_soup)
        elems = response_soup.select("body > div > div > div > script[type]")
        token_pattern = re.compile(r"\"(\w{32})\"")
        access_token = token_pattern.search(str(elems[0])).group(1)
        if access_token is None:
            raise Exception("获取 Steam 聊天 access_token 失败！")
        else:
            return access_token

    """
    @description: 访问 API 以执行类似打开聊天窗口、发信等行为
    -------
    @param:
    -------
    @return:
    """
    def _api_call(self, endpoint, params, timeout_ignore=False):
        print(endpoint, params)
        response = self._session.post(endpoint, data=params)
        response.raise_for_status()
        response_status = response.json().get("error")
        if timeout_ignore and response_status == "Timeout":
            return
        elif response_status != "OK":
            raise Exception(response_status)
        else:
            return response

    """
    @description: 登录 Steam 聊天界面
    -------
    @param:
    -------
    @return:
    """
    def _login(self, ui_mode="web"):
        self._chat_params["ui_mode"] = ui_mode
        self._chat_params["access_token"] = self._get_access_token()
        endpoint = Endpoints.CHAT_LOGIN
        params = {"ui_mode": self._chat_params.get("ui_mode"),
                  "access_token": self._chat_params.get("access_token")}
        response = self._api_call(endpoint, params)
        self._chat_params.update(response.json())
        return response

    """
    @description: 退出 Steam 聊天界面
    -------
    @param:
    -------
    @return:
    """
    def _logout(self):
        endpoint = Endpoints.CHAT_LOGOUT
        params = {"access_token": self._chat_params.get("access_token"),
                  "umqid": self._chat_params.get("umqid")}
        self._chat_params = {}
        return self._api_call(endpoint, params)

    """
    @description: 向指定用户发送信息，用户以 Steam 64 位 ID 作唯一区分
    -------
    @param:
    -------
    @return:
    """
    def send_message(self, steamid_64, text):
        endpoint = Endpoints.SEND_MESSAGE
        params = {"access_token": self._chat_params.get("access_token"),
                  "steamid_dst": steamid_64,
                  "text": text,
                  "type": "saytext",
                  "umqid": self._chat_params.get("umqid")}
        return self._api_call(endpoint, params)

    """
    @description: 轮询行为？
    -------
    @param:
    -------
    @return:
    """
    def poll_events(self) -> dict:
        endpoint = Endpoints.CHAT_POLL
        params = {"access_token": self._chat_params.get("access_token"),
                  "umqid": self._chat_params.get("umqid"),
                  "message": self._chat_params.get("message"),
                  "pollid": 1,
                  "sectimeout": 20,
                  "secidletime": 0,
                  "use_accountids": 1}
        response = self._api_call(endpoint, params, timeout_ignore=True)
        if not response:
            return {}
        data = response.json()
        self._chat_params["message"] = data["messagelast"]
        return response.json()

    """
    @description: 获取聊天消息
    -------
    @param:
    -------
    @return:
    """
    def fetch_messages(self) -> dict:
        message_list = {
            'sent': [],
            'received': []
        }
        events = self.poll_events()
        if not events:
            return message_list
        # 获取 Steam 聊天信息
        messages = events["messages"]
        for message in messages:
            text = message.get("text")
            # 对方发的信息
            if message['type'] == "saytext":
                accountid_from = account_id_to_steam_id(
                    message.get("accountid_from"))
                message_list['received'].append({"partner": accountid_from,
                                                 "message": text})
            # 我方发的信息
            elif message['type'] == "my_saytext":
                accountid_from = account_id_to_steam_id(
                    message.get("accountid_from"))
                message_list['sent'].append({"partner": accountid_from,
                                             "message": text})
        return message_list


"""
@description: 单体测试
-------
@param:
-------
@return:
"""
if __name__ == "__main__":
    print("todo...")
