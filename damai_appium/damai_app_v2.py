# -*- coding: UTF-8 -*-
"""
__Author__ = "BlueCestbon"
__Version__ = "2.0.0"
__Description__ = "大麦app抢票自动化 - 优化版"
__Created__ = 2025/09/13 19:27
"""

import time
from appium import webdriver
from appium.options.common.base import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import Config


class DamaiBot:
    """大麦 APP 抢票主流程。

    重构要点：
    - driver 不再在 __init__ 里直接连接，由调用方通过 attach() 注入或
      显式 setup()，便于复用 driver 跨多次抢票轮询，避免 UiAutomator2
      起新 session 的 5-10 秒固定开销
    - run_ticket_grabbing 的 finally 不再无脑 driver.quit()，
      抢到票后用户需要在 APP 内手动确认订单状态
    """

    def __init__(self, driver=None):
        self.config = Config.load_config()
        self.driver = driver
        self.wait = None
        if driver is not None:
            self._apply_perf_settings()

    def setup(self):
        """显式建立 Appium 连接。仅在调用方未通过 attach 注入 driver 时使用。"""
        if self.driver is not None:
            return
        capabilities = {
            "platformName": "Android",
            "platformVersion": "16",
            "deviceName": "emulator-5554",
            "appPackage": "cn.damai",
            "appActivity": ".launcher.splash.SplashMainActivity",
            "unicodeKeyboard": True,
            "resetKeyboard": True,
            "noReset": True,
            "newCommandTimeout": 6000,
            "automationName": "UiAutomator2",
            "skipServerInstallation": False,
            "ignoreHiddenApiPolicyError": True,
            "disableWindowAnimation": True,
            "mjpegServerFramerate": 1,
            "adbExecTimeout": 20000,
        }
        device_app_info = AppiumOptions()
        device_app_info.load_capabilities(capabilities)
        self.driver = webdriver.Remote(self.config.server_url, options=device_app_info)
        self._apply_perf_settings()

    def _apply_perf_settings(self):
        """对 driver 套用抢票场景的性能调优。driver 已就绪时由 setup 或 attach 调用。"""
        self.driver.update_settings({
            "waitForIdleTimeout": 0,
            "actionAcknowledgmentTimeout": 0,
            "keyInjectionDelay": 0,
            "waitForSelectorTimeout": 300,
            "ignoreUnimportantViews": False,
            "allowInvisibleElements": True,
            "enableNotificationListener": False,
        })
        self.wait = WebDriverWait(self.driver, 2)

    def close(self):
        """显式关闭 driver。由调用方在确认抢票流程整体结束后触发。"""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def ultra_fast_click(self, by, value, timeout=1.5):
        """超快速点击 - 适合抢票场景"""
        try:
            # 直接查找并点击，不等待可点击状态
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            # 使用坐标点击更快
            rect = el.rect
            x = rect['x'] + rect['width'] // 2
            y = rect['y'] + rect['height'] // 2
            self.driver.execute_script("mobile: clickGesture", {
                "x": x,
                "y": y,
                "duration": 50  # 极短点击时间
            })
            return True
        except TimeoutException:
            return False

    def batch_click(self, elements_info, delay=0.1):
        """批量点击操作"""
        for by, value in elements_info:
            if self.ultra_fast_click(by, value):
                if delay > 0:
                    time.sleep(delay)
            else:
                print(f"点击失败: {value}")

    def ultra_batch_click(self, elements_info, timeout=2):
        """超快批量点击 - 带等待机制"""
        coordinates = []
        # 批量收集坐标，带超时等待
        for by, value in elements_info:
            try:
                # 等待元素出现
                el = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                rect = el.rect
                x = rect['x'] + rect['width'] // 2
                y = rect['y'] + rect['height'] // 2
                coordinates.append((x, y, value))
            except TimeoutException:
                print(f"超时未找到用户: {value}")
            except Exception as e:
                print(f"查找用户失败 {value}: {e}")
        print(f"成功找到 {len(coordinates)} 个用户")
        # 快速连续点击
        for i, (x, y, value) in enumerate(coordinates):
            self.driver.execute_script("mobile: clickGesture", {
                "x": x,
                "y": y,
                "duration": 30
            })
            if i < len(coordinates) - 1:
                time.sleep(0.01)
            print(f"点击用户: {value}")

    def smart_wait_and_click(self, by, value, backup_selectors=None, timeout=1.5):
        """智能等待和点击 - 支持备用选择器"""
        selectors = [(by, value)]
        if backup_selectors:
            selectors.extend(backup_selectors)

        for selector_by, selector_value in selectors:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((selector_by, selector_value))
                )
                rect = el.rect
                x = rect['x'] + rect['width'] // 2
                y = rect['y'] + rect['height'] // 2
                self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 50})
                return True
            except TimeoutException:
                continue
        return False

    def run_ticket_grabbing(self):
        """执行抢票主流程"""
        try:
            print("开始抢票流程...")
            start_time = time.time()

            # 1. 城市选择 - 准备多个备选方案
            print("选择城市...")
            city_selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{self.config.city}")'),
                (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{self.config.city}")'),
                (By.XPATH, f'//*[@text="{self.config.city}"]')
            ]
            if not self.smart_wait_and_click(*city_selectors[0], city_selectors[1:]):
                print("城市选择失败")
                return False

            # 2. 点击预约按钮 - 多种可能的按钮文本
            print("点击预约按钮...")
            book_selectors = [
                (By.ID, "cn.damai:id/trade_project_detail_purchase_status_bar_container_fl"),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*预约.*|.*购买.*|.*立即.*")'),
                (By.XPATH, '//*[contains(@text,"预约") or contains(@text,"购买")]')
            ]
            if not self.smart_wait_and_click(*book_selectors[0], book_selectors[1:]):
                print("预约按钮点击失败")
                return False

            # 3. 票价选择 - 优化查找逻辑
            print("选择票价...")
            try:
                # 直接尝试点击，不等待容器，实际每次都失败，只能等待
                price_container = self.driver.find_element(By.ID, 'cn.damai:id/project_detail_perform_price_flowlayout')
                # price_container = self.wait.until(  # 等待找到容器
                #     EC.presence_of_element_located((By.ID, 'cn.damai:id/project_detail_perform_price_flowlayout')))
                # 在容器内找 index=1 且 clickable="true" 的 FrameLayout【因为799元的票价是排在第二的，但是page里text是空的被隐藏了】
                target_price = price_container.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().className("android.widget.FrameLayout").index({self.config.price_index}).clickable(true)'
                )
                self.driver.execute_script('mobile: clickGesture', {'elementId': target_price.id})
            except Exception as e:
                print(f"票价选择失败，启动备用方案: {e}")
                # 备用方案
                # 先找到大容器
                price_container = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'cn.damai:id/project_detail_perform_price_flowlayout')))
                # 在容器内找 index=1 且 clickable="true" 的 FrameLayout【因为799元的票价是排在第二的，但是page里text是空的被隐藏了】
                target_price = price_container.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().className("android.widget.FrameLayout").index({self.config.price_index}).clickable(true)'
                )
                self.driver.execute_script('mobile: clickGesture', {'elementId': target_price.id})

                # if not self.ultra_fast_click(AppiumBy.ANDROID_UIAUTOMATOR,
                #                              'new UiSelector().textMatches(".*799.*|.*\\d+元.*")'):
                #     return False

            # 4. 数量选择
            print("选择数量...")
            if self.driver.find_elements(by=By.ID, value='layout_num'):
                clicks_needed = len(self.config.users) - 1
                if clicks_needed > 0:
                    try:
                        plus_button = self.driver.find_element(By.ID, 'img_jia')
                        for i in range(clicks_needed):
                            rect = plus_button.rect
                            x = rect['x'] + rect['width'] // 2
                            y = rect['y'] + rect['height'] // 2
                            self.driver.execute_script("mobile: clickGesture", {
                                "x": x,
                                "y": y,
                                "duration": 50
                            })
                            time.sleep(0.02)
                    except Exception as e:
                        print(f"快速点击加号失败: {e}")

            # if self.driver.find_elements(by=By.ID, value='layout_num') and self.config.users is not None:
            #     for i in range(len(self.config.users) - 1):
            #         self.driver.find_element(by=By.ID, value='img_jia').click()

            # 5. 确定购买
            print("确定购买...")
            if not self.ultra_fast_click(By.ID, "btn_buy_view"):
                # 备用按钮文本
                self.ultra_fast_click(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*确定.*|.*购买.*")')

            # 6. 批量选择用户
            print("选择用户...")
            user_clicks = [(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{user}")') for user in
                           self.config.users]
            # self.batch_click(user_clicks, delay=0.05)  # 极短延迟
            self.ultra_batch_click(user_clicks)

            # 7. 提交订单
            print("提交订单...")
            submit_selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("立即提交")'),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*提交.*|.*确认.*")'),
                (By.XPATH, '//*[contains(@text,"提交")]')
            ]
            self.smart_wait_and_click(*submit_selectors[0], submit_selectors[1:])

            end_time = time.time()
            print(f"抢票流程完成，耗时: {end_time - start_time:.2f}秒")
            return True

        except Exception as e:
            print(f"抢票过程发生错误: {e}")
            return False
        # 故意不在 finally 里 driver.quit()：
        # 1. 抢到票后用户需要在 APP 内手动检查/支付订单
        # 2. driver 生命周期由调用方负责，避免每次重试都重建 session

    def run_with_polling(self, max_attempts=20, interval=0.3):
        """轮询模式的抢票。

        相比旧的 run_with_retry（每次失败都关 session + 重建 session +
        重走整条 7 步链路，单次重试开销 5-10 秒），轮询模式复用同一 session，
        在按钮未到位时仅下拉刷新 + 短 sleep，符合大麦开售瞬间的真实节奏。

        max_attempts: 最大轮询次数，默认 20（对应 ~6 秒）
        interval: 每次轮询间隔（秒），默认 0.3
        """
        for attempt in range(1, max_attempts + 1):
            print(f"\n=== 第 {attempt}/{max_attempts} 次尝试 ===")
            if self.run_ticket_grabbing():
                print("抢票成功！请在 APP 内确认订单状态")
                return True
            if attempt >= max_attempts:
                break
            # 模拟下拉刷新让按钮状态更新（票未开售时常见做法）
            try:
                self.driver.swipe(500, 400, 500, 1600, 200)
            except Exception as e:
                print(f"下拉刷新失败: {e}")
            time.sleep(interval)

        print("已达到最大尝试次数，抢票未成功")
        return False


if __name__ == "__main__":
    bot = DamaiBot()
    try:
        bot.setup()
        bot.run_with_polling(max_attempts=20, interval=0.3)
    finally:
        # 整体流程结束后给用户 5 秒缓冲，再关闭 driver
        time.sleep(5)
        bot.close()
