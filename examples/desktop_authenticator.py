#!/usr/bin/env python
# -*- coding:UTF-8 -*-
#
# @AUTHOR: Rabbir
# @FILE: /root/Github/steampy/examples/desktop_authenticator.py
# @DATE: 2021/02/08 Mon
# @TIME: 17:38:52
#
# @DESCRIPTION: Steam 桌面手机令牌 SDA 的测试


# 切换路径到父级
import sys
sys.path.append("..")
from steampy.guard import generate_confirmation_key, generate_one_time_code
from examples import bot_info


# Steam 共享密钥
shared_secret = bot_info.get_shared_secret()
# Steam 身份密钥
identity_secret = bot_info.get_identity_secret()


"""
@description: 测试主方法
-------
@param:
-------
@return:
"""
def main():
    # 获取登录令牌码
    one_time_authentication_code = generate_one_time_code(shared_secret)
    print(one_time_authentication_code)
    # 获取交易确认码
    confirmation_key = generate_confirmation_key(identity_secret, 'conf')
    print(confirmation_key)


"""
@description: 单体测试
-------
@param:
-------
@return:
"""
if __name__ == "__main__":
    main()