import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep

mobile_emulation = {
    "deviceMetrics": { "width": 360, "height": 640, "pixelRatio": 3.0 },
    "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19" }

options = Options()
options.add_experimental_option("mobileEmulation", mobile_emulation)

class Instagram:
    _driver = None
    _status_driver = False
    _status_sign_in = False

    mobile_emulation = {
    "deviceMetrics": { "width": 360, "height": 640, "pixelRatio": 3.0 },
    "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19" }
    options = Options()
    options.add_experimental_option("mobileEmulation", mobile_emulation)

    def _set_driver(self, driver_choice):
        driver_choice = driver_choice.lower()
        if driver_choice == "chrome":
            self._driver = webdriver.Chrome(options = options)
        elif driver_choice == "firefox":
            self._driver = webdriver.Firefox(options = options)
        else:
            print("Please choose 'chrome' or 'firefox'.")
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
            self._driver.find_element_by_xpath('//button[text()="Not Now"]').click()
            sleep(3)
            print("Closed 'Remember the browser' popup.")

        try:
            self._driver.find_element_by_xpath('//button[text()="Add to Home screen"]')
        except:
            pass
        else:
            self._driver.find_element_by_xpath('//button[text()="Cancel"]').click()
            sleep(1)
            print("Closed 'Add Instagram to Home screen' popup.")


if __name__ == "__main__":
    i = Instagram()
    config = i.read_config()
    i.open()
    i.sign_in(config['username'], config['password'])
