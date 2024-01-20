import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import psycopg2
import schedule
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

import time

def scrape_autoria(url):
    driver = webdriver.Chrome() 
    page_url = "https://auto.ria.com/car/used/"
    link_list=[]
    try:
        driver.get(url)
        time.sleep(5)
        ticket_items = driver.find_elements(By.CLASS_NAME, "ticket-item")

        for i in range(len(ticket_items)):
            try:
                href = ticket_items[i].find_element(By.CLASS_NAME, "m-link-ticket").get_attribute("href")
                link_list.append(href)
                print(link_list)
                        
            except StaleElementReferenceException:
                print("StaleElementReferenceException occurred. Retrying...")
                continue

        # No need to navigate back to the original page here
        # driver.get(page_url)


        for car_link in link_list:

            driver.get(car_link)
            time.sleep(5)
            url = car_link
            title = driver.find_element(By.CLASS_NAME, "head").get_attribute("title")
            price_usd = driver.find_element(By.CLASS_NAME, "price_value").text
            odometer = driver.find_element(By.CLASS_NAME, "bold.dhide").text  # Correcting class name
            username = driver.find_element(By.XPATH, '//*[@id="userInfoBlock"]/div[1]/div/h4/a').text  # Using single quotes in XPath
            phone_number = driver.find_element(By.CLASS_NAME, "phone.bold").get_attribute("title")
            images_count = driver.find_element(By.CLASS_NAME, "mhide").get_attribute("title")
            car_number = driver.find_element(By.CLASS_NAME, "head").get_attribute("title")
            car_vin = driver.find_element(By.CLASS_NAME, "vin-code").get_attribute("title")
            datetime_found = datetime.now()

            # Print the extracted information
            print("URL:", url)
            print("Title:", title)
            print("Price (USD):", price_usd)
            print("Odometer:", odometer)
            print("Username:", username)
            print("Phone Number:", phone_number)
            print("Images Count:", images_count)
            print("Car Number:", car_number)
            print("Car VIN:", car_vin)
            print("Datetime Found:", datetime_found)
    finally:
        driver.quit()

scrape_autoria("https://auto.ria.com/car/used/")
