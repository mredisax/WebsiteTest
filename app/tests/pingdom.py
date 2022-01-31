from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from django.conf import settings
import threading
import dns.resolver
import os
import sys
import time
import shutil


class Pingdom():
    def __init__(self, page_url, pingdomtype):
        self.page_url = page_url
        self.pingdomtype = pingdomtype
        self.timestr = time.strftime("%Y%m%d")
        self.path_to_save = f"{settings.MEDIA_ROOT}/test_file/{self.page_url}/{self.page_url}_{self.pingdomtype}"

    def init_chrome(self):
        options = webdriver.ChromeOptions()
        options.add_argument('disable-infobars')
        options.add_argument("window-size=1920x1080")
        options.add_argument("--incognito")
        self.driver = webdriver.Remote(
            command_executor=settings.PINGDOM_SERVER,
            desired_capabilities=options.to_capabilities())
        self.driver.set_window_size(1920, 1080)

    def check_exist_file(self):
        if self.path_to_save:
            if not os.path.exists(f"{self.path_to_save}"):
                return True
            else:
                for f in os.listdir(self.path_to_save):
                    if f.endswith(".png"):
                        shutil.rmtree(f"{self.path_to_save}")
                return True
        return False

    def remove_slash(self, url):
        if "/" in url:
            website_name = url.split("/")
            website_name = website_name[0]
            return website_name
        else:
            return url

    def replace_slash(self, url):
        if "/" in url:
            website_name = url.replace("/", "-")
            return self.path_to_save.replace(self.page_url, website_name)
        else:
            return self.path_to_save

    def pingdom_start(self):
        self.init_chrome()
        self.driver.get("https://tools.pingdom.com/")
        pingdom_url = WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, '//*[@id="urlInput"]')))
        pingdom_url.send_keys(self.page_url)
        pingdom_from = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/app-root/main/app-home-hero/header/section/app-test-runner/div/div[2]/div[2]")))
        pingdom_from.click()
        location = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/app-root/main/app-home-hero/header/section/app-test-runner/div/div[2]/div[2]/app-select/div/div[3]")))
        location.click()

    def pingdom_site(self):
        result=[]
        timestr=time.strftime("%Y%m%d__%H-%M")
        self.path_to_save=self.replace_slash(url=self.page_url)
        time.sleep(1)
        self.pingdom_start()
        page_url_dns=self.remove_slash(url=self.page_url)
        record_a=[rdata for rdata in dns.resolver.resolve(
            str(page_url_dns), "A")]
        i, c = 0, 0 
        if record_a and self.check_exist_file():
            # for i in range(5):
            while i < 5 and c < 30:
                try:
                    start = WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/app-root/main/app-home-hero/header/section/app-test-runner/div/div[2]/div[3]/input")))
                    start.click()
                    time.sleep(45)
                    pingdom_load = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/app-root/main/app-report/section[1]/app-summary/div/div/app-summary-player/div/div[2]/div/div[3]/app-metric/div[2]")))
                    pingdom_load = pingdom_load.text
                    if "ms" not in pingdom_load:
                        pingdom_load=pingdom_load.replace("s", "").strip()
                        pingdom_load=float(pingdom_load) * 1000
                    else:
                        pingdom_load=pingdom_load.replace("ms", "").strip()
                    result.append(pingdom_load)
                    print(f"{self.page_url} - {pingdom_load}")
                    if not os.path.exists(f"{self.path_to_save}"):
                        os.makedirs(f"{self.path_to_save}")
                    self.driver.get_screenshot_as_file(
                        f"{self.path_to_save}/{timestr}_{page_url_dns}_pingdom_{self.pingdomtype}_{str(i+1)}__{pingdom_load}.png")
                    time.sleep(20)
                except Exception as e:
                    time.sleep(5)
                    print(f"error {e}")
                    error_page = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "/html/body/app-root/main/app-home-hero/header/section/app-test-runner/div")))
                    if error_page:
                        print("try again")
                        self.pingdom_start()
                        time.sleep(20)
                        c += 1
                        continue
                i += 1
            print(f"Pingdom for {self.page_url} end")
            shutil.make_archive(f"{self.path_to_save}",
                                "zip", f"{self.path_to_save}")
            print("proba zapisu")
            try:
                shutil.rmtree(f"{self.path_to_save}")
            except Exception as e:
                print(f"error {e}")
                self.driver.quit()
            self.driver.quit()
            return result
        else:
            print(
                f"Brak rekordu A dla {self.page_url} lub jest problem z utworzeniem katalogu")
            self.driver.quit()
            return False
