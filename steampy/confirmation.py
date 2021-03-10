#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# @AUTHOR: Rabbir
# @FILE: /root/Github/steampy/steampy/confirmation.py
# @DATE: 2021/03/10 Wed
# @TIME: 16:13:04
#
# @DESCRIPTION: Steam 交易确认模块


import enum
import json
import time
import requests
from typing import List
from bs4 import BeautifulSoup
from steampy import guard
from steampy.exceptions import ConfirmationExpected
from steampy.login import InvalidCredentials


"""
@description: 交易类
-------
@param:
-------
@return:
"""
class Confirmation:

    """
    @description: 初始化
    -------
    @param:
    -------
    @return:
    """
    def __init__(self, _id, data_confid, data_key):
        self.id = _id.split("conf")[1]
        self.data_confid = data_confid
        self.data_key = data_key


"""
@description: 标签
-------
@param:
-------
@return:
"""
class Tag(enum.Enum):
    CONF = "conf"
    DETAILS = "details"
    ALLOW = "allow"
    CANCEL = "cancel"


"""
@description: 交易确认器类
-------
@param:
-------
@return:
"""
class ConfirmationExecutor:

    # 交易确认链接
    CONF_URL = "https://steamcommunity.com/mobileconf"

    """
    @description: 初始化
    -------
    @param:
    -------
    @return:
    """
    def __init__(self,
                 identity_secret: str,
                 my_steam_id: str,
                 session: requests.Session) -> None:
        # 我的 Steam ID
        self._my_steam_id = my_steam_id
        # Steam 身份密钥
        self._identity_secret = identity_secret
        # 会话 Session
        self._session = session

    """
    @description: 发送允许交易的请求
    -------
    @param:
    -------
    @return:
    """
    def send_trade_allow_request(self, trade_offer_id: str) -> dict:
        # 获取所有待确认的交易
        confirmations = self._get_confirmations()
        # 根据交易 ID 获取交易
        confirmation = self._select_trade_offer_confirmation(confirmations,
                                                             trade_offer_id)
        return self._send_confirmation(confirmation)

    """
    @description: 确认出售的请求
    -------
    @param:
    -------
    @return:
    """
    def confirm_sell_listing(self, asset_id: str) -> dict:
        # 获取所有待确认的交易
        confirmations = self._get_confirmations()
        # 获取出售的待确认交易
        confirmation = self._select_sell_listing_confirmation(confirmations,
                                                              asset_id)
        return self._send_confirmation(confirmation)

    """
    @description: 确认交易
    -------
    @param:
    -------
    @return:
    """
    def _send_confirmation(self, confirmation: Confirmation) -> dict:
        tag = Tag.ALLOW
        params = self._create_confirmation_params(tag.value)
        params["op"] = tag.value,
        params["cid"] = confirmation.data_confid
        params["ck"] = confirmation.data_key
        headers = {"X-Requested-With": "XMLHttpRequest"}
        response = self._session.get(self.CONF_URL + "/ajaxop",
                                     params=params,
                                     headers=headers).json()
        return response

    """
    @description: 获取当前所有待确认的交易
    -------
    @param:
    -------
    @return:
    """
    def _get_confirmations(self) -> List[Confirmation]:
        confirmations = []
        # 获取待确认的交易界面并解析
        confirmations_page = self._fetch_confirmations_page()
        soup = BeautifulSoup(confirmations_page.text, "html.parser")
        # 如果没有待确认的交易，返回空列表
        if soup.select("#mobileconf_empty"):
            return confirmations
        # 如果有待确认的交易
        for confirmation_div in soup.select(
                "#mobileconf_list .mobileconf_list_entry"):
            _id = confirmation_div["id"]
            data_confid = confirmation_div["data-confid"]
            data_key = confirmation_div["data-key"]
            # 创建交易对象类并加入结果列表
            confirmations.append(Confirmation(_id, data_confid, data_key))
        return confirmations

    """
    @description: 获取 Steam 交易确认界面
    -------
    @param:
    -------
    @return:
    """
    def _fetch_confirmations_page(self) -> requests.Response:
        tag = Tag.CONF.value
        # 获取
        params = self._create_confirmation_params(tag)
        # 请求头
        headers = {"X-Requested-With": "com.valvesoftware.android.steam.community"}
        response = self._session.get(self.CONF_URL + "/conf",
                                     params=params,
                                     headers=headers)
        # 访问出错的情况
        if (("Steam Guard Mobile Authenticator is providing incorrect " \
                + "Steam Guard codes.") in response.text):
            raise InvalidCredentials("Invalid Steam Guard file")
        return response

    """
    @description: 获取 Steam 交易的详细内容页面
    -------
    @param:
    -------
    @return:
    """
    def _fetch_confirmation_details_page(self, confirmation: Confirmation) -> str:
        tag = "details" + confirmation.id
        params = self._create_confirmation_params(tag)
        response = self._session.get(self.CONF_URL \
                                     + "/details/" \
                                     + confirmation.id,
                                     params=params)
        return response.json()["html"]

    """
    @description: 创建交易类对象
    -------
    @param:
    -------
    @return:
    """
    def _create_confirmation_params(self, tag_string: str) -> dict:
        timestamp = int(time.time())
        # 生成当前时间的交易确认码
        confirmation_key = guard.generate_confirmation_key(
            self._identity_secret, tag_string, timestamp)
        # 生成设备 ID
        android_id = guard.generate_device_id(self._my_steam_id)
        return {"p": android_id,
                "a": self._my_steam_id,
                "k": confirmation_key,
                "t": timestamp,
                "m": "android",
                "tag": tag_string}

    """
    @description: 根据交易 ID 获取交易
    -------
    @param:
    -------
    @return:
    """
    def _select_trade_offer_confirmation(self,
                                         confirmations: List[Confirmation],
                                         trade_offer_id: str) -> Confirmation:
        # 遍历所有交易
        for confirmation in confirmations:
            # 交易详细页面
            confirmation_details_page = self._fetch_confirmation_details_page(
                confirmation)
            # 获取这个详细页面内的交易 ID
            confirmation_id = self._get_confirmation_trade_offer_id(
                confirmation_details_page)
            if confirmation_id == trade_offer_id:
                return confirmation
        # 未找到对应交易
        raise ConfirmationExpected

    """
    @description: 获取待确认的出售交易确认
    -------
    @param:
    -------
    @return:
    """
    def _select_sell_listing_confirmation(self,
                                          confirmations: List[Confirmation],
                                          asset_id: str) -> Confirmation:
        # 遍历所有交易
        for confirmation in confirmations:
            # 交易详细页面
            confirmation_details_page = self._fetch_confirmation_details_page(
                confirmation)
            # 获取这个详细页面内的出售确认 ID
            confirmation_id = self._get_confirmation_sell_listing_id(
                confirmation_details_page)
            if confirmation_id == asset_id:
                return confirmation
        # 未找到对应交易
        raise ConfirmationExpected

    """
    @description: 从页面中解析出售确认 ID
    -------
    @param:
    -------
    @return:
    """
    @staticmethod
    def _get_confirmation_sell_listing_id(confirmation_details_page: str) -> str:
        soup = BeautifulSoup(confirmation_details_page, 'html.parser')
        scr_raw = soup.select("script")[2].text.strip()
        scr_raw = scr_raw[scr_raw.index("'confiteminfo', ") + 16:]
        scr_raw = scr_raw[:scr_raw.index(", UserYou")].replace("\n", "")
        return json.loads(scr_raw)["id"]

    """
    @description: 从页面中解析交易确认 ID
    -------
    @param:
    -------
    @return:
    """
    @staticmethod
    def _get_confirmation_trade_offer_id(confirmation_details_page: str) -> str:
        soup = BeautifulSoup(confirmation_details_page, 'html.parser')
        full_offer_id = soup.select('.tradeoffer')[0]['id']
        return full_offer_id.split('_')[1]
