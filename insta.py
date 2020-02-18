import os
import json
import datetime
import re
import urllib.request
from time import sleep
from math import ceil

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

import pyautogui


class Instagram:
    _driver = None
    _status_driver = False
    _status_sign_in = False
    posts = {}

    mobile_emulation = {
        "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
        "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) "
                     "AppleWebKit/535.19 (KHTML, like Gecko) "
                     "Chrome/18.0.1025.166 Mobile Safari/535.19"}
    _options = Options()
    _options.add_experimental_option("mobileEmulation", mobile_emulation)

    def _set_driver(self, driver_choice):
        driver_choice = driver_choice.lower()
        if driver_choice == "chrome":
            self._driver = webdriver.Chrome(options=self._options)
        elif driver_choice == "firefox":
            self._driver = webdriver.Firefox(options=self._options)
        else:
            print("Please choose 'chrome' or 'firefox'.")
            return False
        return True

    def open(self, driver_choice="chrome"):
        try:
            self._set_driver(driver_choice)
            print("Program started.")
            print("Driver: {}.".format(driver_choice))
            self._status_driver = True
            return True
        except Exception as exp:
            print(exp)
            self._status_driver = False
            return False

    @staticmethod
    def read_config():
        if not os.path.isfile("config.json"):
            print("There is no config.json file found.")
            return None
        else:
            try:
                with open("config.json") as data_file:
                    data = json.load(data_file)
                    if not data["username"]:
                        print("Couldn't localize username.")
                    if not data["password"]:
                        print("Couldn't localize password.")
                return data
            except:
                return None

    def sign_in(self, username, password):
        if not self._status_driver:
            self._status_sign_in = False
            return False
        try:
            self._driver.get("https://www.instagram.com/accounts/login")
            sleep(2)

            # Send username and password
            self._driver.find_element_by_name("username").send_keys(username)
            self._driver.find_element_by_name("password").send_keys(password)
            self._driver.find_element_by_css_selector("button[type='submit']").click()
            sleep(5)

            # 2FA
            try:
                self._driver.find_element_by_name("verificationCode")
                try:
                    code = input("Enter the verification code.")
                    self._driver.find_element_by_name("verificationCode").send_keys(code)
                    self._driver.find_element_by_css_selector("button[type='button']").click()
                    sleep(6)

                    self.close_popups()
                    self._driver.find_element_by_css_selector("a[href='/explore/']")
                    print("Successfully logged in.")
                    self._status_sign_in = True
                    return True

                except Exception as exp:
                    print("Verification unsuccessful.")
                    self._status_sign_in = False
                    return False
            except:
                pass  # If no 2FA enabled.

            try:
                self.close_popups()
                self._driver.find_element_by_css_selector("a[href='/explore/']")
                print("Successfully logged in.")
                self._status_sign_in = True
                return True
            except:
                pass

            print("Wrong username or password!")
            return False

        except Exception as exp:
            print(exp)
            self._status_sign_in = False
            return False

    def close_popups(self):
        try:
            self._driver.find_element_by_class_name("coreSpriteKeyhole")
        except:
            pass
        else:
            self._driver.find_element_by_xpath("//button[text()='Not Now']").click()
            sleep(3)
            print("Closed 'Remember the browser' popup.")

        try:
            self._driver.find_element_by_xpath("//button[text()='Add to Home screen']")
        except:
            pass
        else:
            self._driver.find_element_by_xpath("//button[text()='Cancel']").click()
            sleep(1)
            print("Closed 'Add Instagram to Home screen' popup.")

    def find_images(self, page_name, recency):
        """
        Finds image and checks it's like count.

        :param page_name:
        :param recency: max days to be taken into search scope
        :return:
        """
        date = datetime.datetime.now()
        self._driver.get("https://www.instagram.com/{}/feed/".format(page_name))
        sleep(3)
        recent = True
        while recent:
            dates = self._driver.find_elements_by_xpath("//time")
            for el in dates:
                # Get post time
                post_time = el.get_attribute("datetime")  # datetime as `str`
                post_time = datetime.datetime.strptime(post_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                delta = date - post_time  # Compose recency condition

                if delta.days < recency:
                    base = el.find_element_by_xpath("..")
                    post_addr = base.get_attribute("href")
                    post_id = re.search('(?<=/p/)(.*)(?=/)', post_addr).group(1)

                    like_path = "//a[@href='/p/{}/liked_by/']/span".format(post_id)
                    views_path = "../../..//span[text()[contains(., 'views')]]"
                    try:
                        like_el = self._driver.find_element_by_xpath(like_path).text
                    except:
                        likes_el = el.find_element_by_xpath(views_path).text
                        likes = int(''.join(re.findall('\d+', likes_el)))
                    else:
                        likes = int(''.join(re.findall('\d+', like_el)))
                    self.posts[post_id] = {'likes': likes}
                else:
                    recent = False

            self._driver.execute_script("arguments[0].scrollIntoView();", dates[-1])
            sleep(1)
        self.save_best_posts()

    def save_best_posts(self, threshold=0.2):
        assert 0 < threshold < 1, "Wrong threshold value. Use decimal value between 0 and 1. Default: 0.2"
        number = ceil(len(self.posts) * threshold)  # Grab x% of best posts.
        print("Saving {} posts.".format(number))
        while number > 0:
            all_likes = [post['likes'] for post in self.posts.values()]
            for pid, post in self.posts.items():
                if post['likes'] == max(all_likes):
                    self.save_post(pid)
                    print("Saved a post. ID: {}, with {} likes.".format(pid, post['likes']))
                    self.posts[pid]['likes'] = 0  # Ensure picked post won't be picked again.
                    number -= 1

    def save_post(self, pid):
        looking_for_el = True
        top = self._driver.find_element_by_tag_name("main")
        self._driver.execute_script("arguments[0].scrollIntoView();", top)
        while looking_for_el:
            try:
                element = self._driver.find_element_by_xpath("*//a[@href='/p/{}/']/time".format(pid))
                self._driver.execute_script("arguments[0].scrollIntoView();", element)
                self._driver.execute_script("window.scrollBy(0, -200);")  # Get save button into view.
            except:
                print("Can't locate the post.")
                self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            else:
                looking_for_el = False
        save_path = "./../../..//*[name()='svg'][@aria-label='Save']"
        element.find_element_by_xpath(save_path).click()  # Save!


if __name__ == "__main__":
    i = Instagram()
    config = i.read_config()
    i.open()
    i.sign_in(config["username"], config["password"])
    i.find_images('spicybaristamemes', 30)