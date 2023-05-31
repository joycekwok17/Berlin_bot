import time
import os
import logging
from platform import system
import pygame
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Process
import random

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
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a')))
        driver.find_element(By.XPATH, '//*[@id="mainForm"]/div/div/div/div/div/div/div/div/div/div[1]/div[1]/div[2]/a').click()
        time.sleep(5)

    @staticmethod
    def tick_off_some_bullshit(driver: webdriver.Chrome):
        logging.info("Ticking off agreement")
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="xi-div-1"]/div[4]/label[2]/p')))
        driver.find_element(By.XPATH, '//*[@id="xi-div-1"]/div[4]/label[2]/p').click()
        time.sleep(1)
        driver.find_element(By.ID, 'applicationForm:managedForm:proceed').click()
        time.sleep(5)

    @staticmethod
    def enter_form(driver: webdriver.Chrome):
        logging.info("Fill out form")
        # select china
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'xi-sel-400')))
        s = Select(driver.find_element(By.ID, 'xi-sel-400'))
        s.select_by_visible_text("China")
        # eine person
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'xi-sel-422')))
        s = Select(driver.find_element(By.ID, 'xi-sel-422'))
        s.select_by_visible_text("eine Person")
        # no family
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.ID, 'xi-sel-427')))
        s = Select(driver.find_element(By.ID, 'xi-sel-427'))
        s.select_by_visible_text("nein")
        time.sleep(5)

        # apply for a residence permit
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="xi-div-30"]/div[1]/label/p')))
        driver.find_element(By.XPATH, '//*[@id="xi-div-30"]/div[1]/label/p').click()
        time.sleep(2)

        # click on employment group
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="inner-479-0-1"]/div/div[3]/label/p')))
        driver.find_element(By.XPATH, '//*[@id="inner-479-0-1"]/div/div[3]/label/p').click()
        time.sleep(2)

        # b/c of employment
        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="inner-479-0-1"]/div/div[4]/div/div[4]/label')))
        driver.find_element(By.XPATH, '//*[@id="inner-479-0-1"]/div/div[4]/div/div[4]/label').click()
        time.sleep(4)

    def _success(self):
        logging.info("!!!SUCCESS - do not close the window!!!!")
        while True:
            self._play_sound_linux(self._sound_file)
            time.sleep(15)

        # todo play something and block the browser

    def run_once(self):
        with WebDriver() as driver:
            while True:
                try:
                    self.enter_start_page(driver)
                    self.tick_off_some_bullshit(driver)
                    self.enter_form(driver)
                    if not self._error_message in driver.page_source:
                        self._success()
                    logging.info("Retry submitting form")
                    time.sleep(5)
                except TimeoutException:
                    logging.info("Timeout exceeded, starting another round")
                    break

    def run_loop(self):
        # play sound to check if it works
        self._play_sound_linux(self._sound_file)
        while True:
            logging.info("One more round")
            processes = []
            for _ in range(5):
                delay = random.randint(1, 10)  # Random delay between 1 and 10 seconds
                process = Process(target=self.run_once)
                processes.append(process)
                process.start()
                time.sleep(delay)

            for process in processes:
                process.join()

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
