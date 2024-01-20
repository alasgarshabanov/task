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
import time

# PostgreSQL connection 
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "autoria_db"
DB_USER = "user_autoria"
DB_PASSWORD = "h9di905w9RRAC39"

def create_table():
    connection = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = connection.cursor()

    create_table_query = '''
        CREATE TABLE IF NOT EXISTS cars (
            id SERIAL PRIMARY KEY,
            url VARCHAR(255),
            title VARCHAR(255),
            price_usd VARCHAR(255),
            odometer VARCHAR(255),
            username VARCHAR(255),
            phone_number VARCHAR(15),
            image_url VARCHAR(255),
            images_count NUMERIC,
            car_number VARCHAR(20),
            car_vin VARCHAR(50),
            datetime_found TIMESTAMP
        );
    '''
    cursor.execute(create_table_query)
    connection.commit()
    connection.close()

def insert_data(data):
    connection = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = connection.cursor()

    insert_query = '''
        INSERT INTO cars (url, title, price_usd, odometer, username, phone_number, image_url, images_count, car_number, car_vin, datetime_found)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    '''
    cursor.execute(insert_query, tuple(data.values()))
    connection.commit()
    connection.close()

def scrape_autoria(url):
    driver = webdriver.Chrome()

    try:
        driver.get(url)
        time.sleep(5) 

        car_sections = driver.find_elements(By.CLASS_NAME, 'ticket-item')

        for car_section in car_sections:
            car_link = car_section.find_element(By.CLASS_NAME, 'm-link-ticket')
            car_link.click()
            time.sleep(2)  

            driver.switch_to.window(driver.window_handles[1])

            data = extract_data_from_individual_page(driver.page_source)
            insert_data(data)
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        next_page_link = driver.find_element(By.CSS_SELECTOR, 'a.js-next')
        if next_page_link:
            next_page_url = next_page_link.get_attribute('href')
            scrape_autoria(next_page_url)

    finally:
        driver.quit()

def extract_data_from_individual_page(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')

    data = {
        'url': soup.find('link', rel='canonical')['href'],
        'title': soup.select_one('h1.head-ticket').text.strip(),
    }

    print(data)

    return data

def extract_data_from_section(car_section):
    data = {
        'url': car_section.select_one('a.m-link-ticket')['href'],
        'title': car_section.select_one('a.address span.blue.bold').text.strip(),
        'price_usd': float(re.sub(r'[^0-9.]', '', car_section.select_one('span.bold.size22.green[data-currency="USD"]').text)),
        'odometer': float(car_section.select_one('li.js-race').text.split()[0].replace(',', '')),
        'username': car_section.select_one('div.up-my-offer.person-block.hide').text.strip(),
        'phone_number': car_section.select_one('li.js-phone').text.strip() if car_section.select_one('li.js-phone') else '',
        'image_url': car_section.select_one('a.photo-185x120')['href'],
        'images_count': int(car_section.select_one('div.ticket-photo.loaded')['data-photocount']) if car_section.select_one('div.ticket-photo.loaded') else 0,
        'car_number': car_section.select_one('div.base_information span.vin-code').text.strip() if car_section.select_one('div.base_information span.vin-code') else '',
        'car_vin': car_section.select_one('div.base_information span.vin-code').text.strip() if car_section.select_one('div.base_information span.vin-code') else '',
        'datetime_found': extract_datetime(car_section.select_one('span.generateDate').text.strip())
    }

    print(data)

    return data

def extract_datetime(date_string):
    try:
        return datetime.strptime(date_string, '%a %b %d %Y %H:%M:%S %Z%z')
    except ValueError:
        return None  

# perform daily database dump
def dump_database():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    dump_filename = f"dumps/dump_{timestamp}.sql"
    os.system(f"pg_dump -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} > {dump_filename}")

def scrape_and_dump():
    scrape_autoria("https://auto.ria.com/car/used/")
    dump_database()

def main():
    create_table()

    # Schedule the scraping and database dump daily at 00:00
    schedule.every().day.at("00:00").do(scrape_and_dump)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
