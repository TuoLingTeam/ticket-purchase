# -*- coding: UTF-8 -*-
"""
__Author__ = "WECENG"
__Version__ = "1.0.0"
__Description__ = "配置类"
__Created__ = 2023/10/11 18:01
"""


class Config:

    def __init__(self, index_url, login_url, target_url, users, city, dates, prices, if_listen=False, if_commit_order=True, max_retries=1000, fast_mode=True, page_load_delay=2):
        self.index_url = index_url
        self.login_url = login_url
        self.target_url = target_url
        self.users = users
        self.city = city
        self.dates = dates
        self.prices = prices
        # if_listen=True 表示票售完时自动点"缺货登记"，会在大麦后台产生
        # 用户可能不需要的预订单。默认改为 False，避免抢票失败时的副作用
        self.if_listen = if_listen
        self.if_commit_order = if_commit_order
        self.max_retries = max_retries
        self.fast_mode = fast_mode  # 快速模式：减少等待时间和调试输出
        self.page_load_delay = page_load_delay  # 订单确认页加载等待时间（秒）
