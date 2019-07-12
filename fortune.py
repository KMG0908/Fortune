# -*- coding: utf-8 -*-
import json
import re
import requests
import urllib.request
import urllib.parse

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup
from flask import Flask, request
from slack import WebClient
from slack.web.classes import extract_json
from slack.web.classes.blocks import *
from slack.web.classes.elements import *
from slack.web.classes.interactions import MessageInteractiveEvent
from slackeventsapi import SlackEventAdapter

from datetime import datetime, timedelta

SLACK_TOKEN = ?
SLACK_SIGNING_SECRET = ?


app = Flask(__name__)
# /listening 으로 슬랙 이벤트를 받습니다.
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)

user = []

def fortune(data):
    head_section = SectionBlock(
        text = data[1] + "님, 어느 운세를 알고 싶으신가요?"
    )

    # 여러 개의 버튼을 넣을 땐 ActionsBlock을 사용합니다 (버튼 5개까지 가능)
    button_actions = ActionsBlock(
        #block_id=keyword,
        elements=[
            ButtonElement(
                text="오늘의 운세",
                action_id="birth", value="birth"
            ),
            ButtonElement(
                text="띠별 운세", 
                action_id="animal", value="animal"
            ),
            ButtonElement(
                text="별자리 운세",
                action_id="constellation", value="constellation"
            ),
        ]
    )

    # 각 섹션을 list로 묶어 전달합니다
    return [head_section, button_actions]

def today_fortune(id):
    user_ = []
    fortune = []

    for data in user:
        if(id == data[0]):
            user_ = data

    driver = webdriver.Chrome(r'C:\Users\student\Desktop\chatbot\chromedriver.exe')
    driver.get("https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query=%EC%9A%B4%EC%84%B8")

    sex = driver.find_element_by_class_name('_gender')
    driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2]);", sex, 'data-value', user_[4])

    birth = driver.find_element_by_id('srch_txt')
    birth.send_keys(user_[2] + user_[3])

    solar = driver.find_element_by_class_name('luck_month')
    driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2]);", solar, 'data-value', 'solar')

    button = driver.find_element_by_class_name('img_btn')
    button.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "dl._luckText dt.blind"))
    )

    driver.find_element_by_class_name('birth_all').click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "dl._luckText dt.blind"))
    )

    req = driver.page_source
    soup = BeautifulSoup(req, 'html.parser')

    luckText = soup.find('dl', class_="_luckText")
    #fortune.append("`" + luckText.find('dt').get_text() + "`")
    fortune.append("`" + soup.find('div', class_="birth_all").parent.find('span').get_text() + "`")
    fortune.append("*" + luckText.find('strong').get_text() + "*")
    fortune.append(luckText.find('p').get_text())
    fortune.append("\n더 자세히 알고 싶은 부분이 있으신가요?")

    driver.quit()

    head_section = SectionBlock(
        text = '\n'.join(fortune)
    )

    button_actions = ActionsBlock(
        elements=[
            ButtonElement(
                text="애정운", 
                action_id="love", value="love"
            ),
            ButtonElement(
                text="금전운",
                action_id="money", value="money"
            ),
            ButtonElement(
                text="직장운",
                action_id="work", value="work"
            ),
            ButtonElement(
                text="학업, 시험운",
                action_id="study", value="study"
            ),
        ]
    )

    return [head_section, button_actions]
        
def animal_fortune(id):
    user_ = []
    animal_text = []

    for data in user:
        if(id == data[0]):
            user_ = data

    driver = webdriver.Chrome(r'C:\Users\student\Desktop\chatbot\chromedriver.exe')
    driver.get("https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query=%EC%9A%B4%EC%84%B8")

    button = driver.find_element_by_class_name('zo_li')
    button.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "tit"))
    )

    zoo = driver.find_element_by_css_selector('ul.sign_lst li:nth-child(' + str((int(user_[2]) - 4) % 12 + 1) + ') dt.tit')
    zoo.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "_cs_fortune_text"))
    )

    req = driver.page_source
    soup = BeautifulSoup(req, 'html.parser')

    ani = soup.find('li', class_="first_lst")
    animal_text.append("`" + ani.get_text() + "`")

    luckText = soup.find('p', class_="_cs_fortune_text")
    animal_text.append(luckText.get_text())

    yearText = soup.find('dl', class_="_cs_fortune_list")
    years = yearText.find_all('dt')
    texts = yearText.find_all('dd')

    years_ = list(map(lambda x: x.get_text(), years))
    texts_ = list(map(lambda x: x.get_text(), texts))

    for i, data in enumerate(years_):
        if (user_[2] == data[:4]):
            print(years_[i])
            animal_text.append("`" + years_[i] + "` " + texts_[i])

    driver.quit()

    head_section = SectionBlock(
        text = '\n'.join(animal_text)
    )

    return [head_section]


def constellation_fortune(id):
    user_ = []
    constellation_text = []

    date = [["0120", "0218"], ["0219", "0320"], ["0321", "0419"], ["0420", "0520"], ["0521", "0621"], ["0622", "0722"],
            ["0823", "0822"], ["0823", "0923"], ["0924", "1022"], ["1023", "1122"], ["1123", "1224"], ["1225", "0119"]]

    for data in user:
        if(id == data[0]):
            user_ = data

    driver = webdriver.Chrome(r'C:\Users\student\Desktop\chatbot\chromedriver.exe')
    driver.get("https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query=%EC%9A%B4%EC%84%B8")

    button = driver.find_element_by_class_name('con_li')
    button.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "tit"))
    )

    child = ""

    for i, d in enumerate(date):
        if((int(user_[3]) >= int(d[0])) & (int(user_[3]) <= int(d[1]))):
            child = str(i + 1)
            break

    driver.find_element_by_css_selector('ul.sign_lst li:nth-child(' + child + ') dt.tit').click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "_cs_fortune_text"))
    )

    req = driver.page_source
    soup = BeautifulSoup(req, 'html.parser')

    con = soup.find('li', class_="first_lst")
    constellation_text.append("`" + con.get_text() + "`")

    luckText = soup.find('p', class_="_cs_fortune_text")
    constellation_text.append(luckText.get_text())

    driver.quit()

    head_section = SectionBlock(
        text = '\n'.join(constellation_text)
    )

    return [head_section]


def today_fortune_detail(id, select_fortune):
    user_ = []
    birth_fortune = ["love", "money", "work", "study"]
    _fortune = ["birth_love", "birth_money", "birth_company", "birth_study"]
    fortune = []

    for i, x in enumerate(birth_fortune):
        if(select_fortune == x):
            for data in user:
                if(id == data[0]):
                    user_ = data

            driver = webdriver.Chrome(r'C:\Users\student\Desktop\chatbot\chromedriver.exe')
            driver.get("https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query=%EC%9A%B4%EC%84%B8")

            sex = driver.find_element_by_class_name('_gender')
            driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2]);", sex, 'data-value', user_[4])

            birth = driver.find_element_by_id('srch_txt')
            birth.send_keys(user_[2] + user_[3])

            solar = driver.find_element_by_class_name('luck_month')
            driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2]);", solar, 'data-value', 'solar')

            button = driver.find_element_by_class_name('img_btn')
            button.click()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "dl._luckText dt.blind"))
            )

            driver.find_element_by_class_name(_fortune[i]).click()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "dl._luckText dt.blind"))
            )

            req = driver.page_source
            soup = BeautifulSoup(req, 'html.parser')

            luckText = soup.find('dl', class_="_luckText")
            #fortune.append("`" + luckText.find('dt').get_text() + "`")
            fortune.append("`" + soup.find('div', class_=_fortune[i]).parent.find('span').get_text() + "`")
            fortune.append(luckText.find('p').get_text())

            driver.quit()
            break

    head_section = SectionBlock(
        text = '\n'.join(fortune)
    )
    
    return [head_section]

# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]
    user_id= event_data["event"]["user"]

    if "운세" in text:
        if(len(user) == 0):
            slack_web_client.chat_postMessage(
                channel=channel,
                text="사용자의 정보가 없어요. 저에게 먼저 정보를 알려주시겠어요? `@fortune <이름> <생년월일(8자리)> <성별(남/여)>`와 같이 멘션해주세요."
            )
            return

        for data in user:
            # 사용자의 정보가 있을 경우
            if(user_id == data[0]):
                message = fortune(data)
                slack_web_client.chat_postMessage(
                    channel=channel,
                    blocks=extract_json(message)
                )
                return
            # 사용자의 정보가 없을 경우
            else:
                slack_web_client.chat_postMessage(
                    channel=channel,
                    text="사용자의 정보가 없어요. 저에게 먼저 정보를 알려주시겠어요? `@fortune <이름> <생년월일(8자리)> <성별(남/여)>`와 같이 멘션해주세요."
                )
                return

    # 사용자가 정보 입력시
    information = text.split('>')[1].strip().split(' ')
    if(len(information) != 3):
        slack_web_client.chat_postMessage(
            channel=channel,
            text="형식이 잘못되었어요! 운세를 알고 싶으시다면 `@fortune 운세`를, 사용자의 정보를 등록하고 싶으시다면 `@fortune <이름> <생년월일(8자리)> <성별(남/여)>`와 같이 멘션해주세요."
        )
        return

    id_ = user_id

    name = information[0]

    if(len(information[1]) == 8):
        try:
            datetime(int(information[1][:4]), int(information[1][4:6]), int(information[1][6:]))
        except ValueError:
            slack_web_client.chat_postMessage(
                channel=channel,
                text="존재하지 않는 날짜에요!"
            )
            return

        birth_year = str(information[1][:4])
        birth_day = str(information[1][4:])
    else:
        slack_web_client.chat_postMessage(
            channel=channel,
            text="생년월일은 8자리로 입력해주세요!"
        )
        return

    if("남" in information[2]):
        gender = "m"
    elif("여" in information[2]):
        gender = "f"
    else:
        slack_web_client.chat_postMessage(
            channel=channel,
            text="성별은 남/여로 입력해주세요!"
        )
        return

    if(len(user) == 0):
        user.append([id_, name, birth_year, birth_day, gender])
    for i, data in enumerate(user):
        # 사용자의 정보가 있는데 새로운 정보를 입력했을 경우
        if(user_id == data[0]):
            user[i] = [id_, name, birth_year, birth_day, gender]

    slack_web_client.chat_postMessage(
        channel=channel,
        text= "*" + name + "* 님의 정보를 기억했어요! `@fortune 운세`와 같이 멘션해주세요."
    )
    return


# 사용자가 버튼을 클릭한 결과는 /click 으로 받습니다
# 이 기능을 사용하려면 앱 설정 페이지의 "Interactive Components"에서
# /click 이 포함된 링크를 입력해야 합니다.
@app.route("/click", methods=["GET", "POST"])
def on_button_click():
    # 버튼 클릭은 SlackEventsApi에서 처리해주지 않으므로 직접 처리합니다
    payload = request.values["payload"]
    click_event = MessageInteractiveEvent(json.loads(payload))

    fortune = click_event.value
    user_id_ = click_event.user.id

    if(fortune == "birth"):
        message = today_fortune(user_id_)
        slack_web_client.chat_postMessage(
            channel=click_event.channel.id,
            blocks=extract_json(message)
        )
        return "OK", 200
    elif(fortune == "animal"):
        message = animal_fortune(user_id_)
        slack_web_client.chat_postMessage(
            channel=click_event.channel.id,
            blocks=extract_json(message)
        )
        return "OK", 200
    elif(fortune == "constellation"):
        message = constellation_fortune(user_id_)
        slack_web_client.chat_postMessage(
            channel=click_event.channel.id,
            blocks=extract_json(message)
        )
        return "OK", 200
    elif fortune in ["love", "money", "work", "study"]:
        message = today_fortune_detail(user_id_, fortune)
        slack_web_client.chat_postMessage(
            channel=click_event.channel.id,
            blocks=extract_json(message)
        )
        return "OK", 200

    # Slack에게 클릭 이벤트를 확인했다고 알려줍니다
    return "OK", 200


# / 로 접속하면 서버가 준비되었다고 알려줍니다.
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('127.0.0.1', port=5000)
