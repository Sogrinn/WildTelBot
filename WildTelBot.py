import time
import datetime
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from telebot import *

token = ''

bot = telebot.TeleBot(token)

User_dict = {}


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Список команд:\n/addnewSKU [SKU]\n/showSKU\n/startTracking\n')
    if message.chat.id not in User_dict.keys():
        User_dict[message.chat.id] = set()


@bot.message_handler(commands=['addnewSKU'])
def new_SKU_message(message):
    SKUForTrackingSet = User_dict[message.chat.id].add(message.text.replace('/addnewSKU', '').strip())


@bot.message_handler(content_types=['document'])
def new_SKU_document(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
    except Exception as e:
        pass
    file = downloaded_file
    xl = pd.ExcelFile(file)
    px = xl.parse()
    User_dict[message.chat.id].add(px.columns[0])
    for SKU in px.get(px.columns[0]):
        User_dict[message.chat.id].add(SKU)


@bot.message_handler(commands=['showSKU'])
def show_SKU(message):
    send_message = ''
    setSKU = User_dict[message.chat.id]
    for SKU in setSKU:
        send_message += f'{SKU}\n'
    bot.send_message(message.chat.id, send_message)


@bot.message_handler(commands=['startTracking'])
def parsing(message):
    while True:
        chat_id = message.chat.id
        for SKU in User_dict[chat_id]:
            url = f'https://www.wildberries.ru/catalog/{SKU}/detail.aspx?targetUrl=BP'
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            driver.get(url)

            time.sleep(1)
            SCROLL_PAUSE_TIME = 0.5
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            name = soup.find('h1', class_='same-part-kt__header')
            product_rating = soup.find('span', class_='user-scores__score')
            comments_list = soup.find_all('li', class_='comments__item feedback')
            for comment in comments_list:
                rate = comment.find('span', class_='feedback__rating stars-line star5')
                text = comment.find('p', class_='feedback__text')
                if rate:
                    continue
                for r in range(1, 5):
                    rate = comment.find('span', class_=f'feedback__rating stars-line star{r}')
                    if rate:
                        rate_for_send = r
                data = comment.find('span', class_='feedback__date hide-desktop')
                send_message = f'Негативный отзыв\n{name.text}\n{product_rating.text}\n{rate_for_send}\n{text.text}'
                bot.send_message(message.chat.id, send_message)
        time.sleep(30)

# Оправку сообщений каждый час можно реализовать через while True и time.sleep + добавить переменную datatime,
# которой будет присваиваться время, в который был начат парсинг и которая будет обновляться каждый час.
# С ней будет сравниваться время комментария, чтобы присылать пользователю только новые комменты



bot.infinity_polling()
