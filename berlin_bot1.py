import time
import os
import logging
import traceback
from platform import system

import pygame
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

system = system()

logging.basicConfig(
    format='%(asctime)s\t%(levelname)s\t%(message)s',
    level=logging.INFO,
)


class WebDriver:
    def __init__(self):
        self._driver: webdriver.Chrome
        self._implicit_wait_time = 20

    def __enter__(self) -> webdriver.Chrome:
        logging.info("Open browser")
        # some stuff that prevents us from being locked out
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        self._driver = webdriver.Chrome(options=options)
        self._driver.implicitly_wait(self._implicit_wait_time)  # seconds
        self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
        return self._driver

    def __exit__(self, exc_type, exc_value, exc_tb):
        logging.info("Close browser")
        self._driver.quit()


class BerlinBot:
    def __init__(self):
        self.wait_time = 20
        self._sound_file = os.path.join(os.getcwd(), "alarm.wav")
        self._error_message = """Für die gewählte Dienstleistung sind aktuell keine Termine frei! Bitte"""

    @staticmethod
    def enter_start_page(driver: webdriver.Chrome):
        logging.info("Visit start page")
        driver.get("https://otv.verwalt-berlin.de/ams/TerminBuchen")
        driver.find_element(By.XPATH,
                            '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a').click()
        time.sleep(5)

    @staticmethod
    def tick_off_some_bullshit(driver: webdriver.Chrome):
        logging.info("Ticking off agreement")
        driver.find_element(By.XPATH, '//*[@id="xi-div-1"]/div[4]/label[2]/p').click()
        time.sleep(1)
        driver.find_element(By.ID, 'applicationForm:managedForm:proceed').click()
        time.sleep(5)

    @staticmethod
    def enter_form(self,driver: webdriver.Chrome):
        logging.info("Fill out form")
        try:
        # select china
            s = Select(driver.find_element(By.ID, 'xi-sel-400'))
            s.select_by_visible_text("China")
            time.sleep(2)
            # eine person
            s = Select(driver.find_element(By.ID, 'xi-sel-422'))
            s.select_by_visible_text("eine Person")
            time.sleep(2)
            # no family
            s = Select(driver.find_element(By.ID, 'xi-sel-427'))
            s.select_by_visible_text("nein")
            time.sleep(5)

            # apply for a residence permit
            driver.find_element(By.XPATH, '//*[@id="xi-div-30"]/div[1]/label/p').click()
            time.sleep(2)

            # click on employment group
            driver.find_element(By.XPATH, '//*[@id="inner-479-0-1"]/div/div[3]/label/p').click()
            time.sleep(2)
            # b/c of employment
            driver.find_element(By.XPATH, '//*[@id="inner-479-0-1"]/div/div[4]/div/div[4]/label').click()
            time.sleep(4)

            # submit form
            # driver.find_element(By.ID, 'applicationForm:managedForm:proceed').click()
            # time.sleep(10)
        except Exception:
            traceback.print_exc()
            self._play_sound_linux(self._sound_file)
            time.sleep(15)

    def _success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        while True:
            self._play_sound_linux(self._sound_file)
            time.sleep(15)

        # todo play something and block the browser

    def run_once(self):
        with WebDriver() as driver:
            self.enter_start_page(driver)
            self.tick_off_some_bullshit(driver)
            # self.enter_form(driver)

            # retry submit
            for _ in range(60):
                logging.info("Retry submitting form")
                self.enter_form(self, driver)
                # driver.find_element(By.ID, 'applicationForm:managedForm:proceed').click()
                time.sleep(10)
                if not self._error_message in driver.page_source:
                    self._success()


    def run_loop(self):
        # play sound to check if it works
        self._play_sound_linux(self._sound_file)
        while True:
            logging.info("One more round")
            self.run_once()
            time.sleep(self.wait_time)

    @staticmethod
    def _play_sound_linux(sound, block=True):
        logging.info("Play sound")
        pygame.mixer.init()
        pygame.mixer.music.load(sound)
        pygame.mixer.music.play()

        if block:
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)



if __name__ == "__main__":
    BerlinBot().run_loop()
