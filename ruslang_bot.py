# Телеграм-бот: пользователь спрашивает бота про один из языков России (включая самоназвания) 
# и получает ответ с разными данными об этом языке, включая ISO-369-3, семью, число носителей, 
# регион, статус, письменность, ссылку на википедию на этом языке, если есть. 

import telebot
import urllib.request
from urllib.error import HTTPError
from lxml import html
import os, os.path
import flask

TOKEN = os.environ["TOKEN"]

bot = telebot.TeleBot(TOKEN, threaded=False)

bot.remove_webhook()
bot.set_webhook(url="https://sheltered-plateau-79499.herokuapp.com/bot")

app = flask.Flask(__name__)

lang_iso = ['abq', 'agx', 'ady', 'ava','ale', 'alr', 'ams', 'ani', 'aqc', 'akv', 'kva', 'bak', 'kap', 'bph', 'bxr', 'vep', 'vvk', 'vot', 'gap', 'gin', 'gdo', 'mrj', 'huz', 'izh', 'inh', 'itl', 'kbd', 'kad', 'kaj', 'xal', 'kpt', 'krc', 'krl', 'ket', 'sjd', 'kpv', 'koi', 'kpy', 'kas', 'kum', 'lbe', 'lez', 'for', 'dar', 'mhr', 'mns', 'meg', 'mdf', 'mui', 'gld', 'nio', 'neg', 'niv', 'nog', 'oaa', 'rut', 'its', 'atv', 'ykg', 'sel', 'stc', 'tab', 'tsr', 'tat', 'ttt', 'tin', 'kim', 'tub', 'tyv', 'yrk', 'udi', 'udm', 'ude', 'ulc', 'utc', 'kjh', 'kca', 'khv', 'tkr', 'ddo', 'rmy', 'cji', 'che', 'chi', 'chv', 'ckt', 'clw', 'cjs', 'evn', 'eve', 'enf', 'myv', 'ess', 'alt', 'yux', 'sah']

def lang_page(): # в этой функции происходит выкачивание страниц языков с web-corpora.net, затем для каждой страницы создается локальная копия; 
    values = {}

    # создаем локальные копии всех доступных страниц с языками (чтобы не нагружать сайт при каждом сообщении пользователя боту)

    # common_url = 'http://web-corpora.net/wsgi3/minorlangs/view/'
    for iso in lang_iso:
        # lang_url = common_url + iso
        # user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
        # req = urllib.request.Request(lang_url, headers={'User-Agent':user_agent})
        # try:
        #     with urllib.request.urlopen(req) as response:
        #         lang_resp = response.read().decode('utf-8')
        #         # f = open('langs' + os.sep + str(iso) + '.html', 'w')
        #         # f.write(lang_resp)
        #         # f.close()
        # except HTTPError as e:
        #     content = e.read()
        try:
            with open('langs' + os.sep + iso + '.html', 'r') as f:
                lang_resp = f.read()
        except:
            print('no lang file ' + iso)

        root = html.fromstring(lang_resp)
        nodes = root.xpath(".//table[contains(@class, 'lang-info')]//tr")
        values[iso] = {}
        for node in nodes:
            td_nodes = node.xpath("td")

            if len(td_nodes) != 2:
                continue

            key = td_nodes[0].text
            value = td_nodes[1].text or ""
            value = value.lower()

            values[iso][key] = value

        wiki_link = root.xpath(".//table[contains(@class, 'lang-info')]//td[@class='wiki']/a")
        try:
            values[iso]['Википедия:'] = wiki_link[0].text
        except:
            pass

    return values

def make_dict(values): # это функция, в которой создается словарь "result": {'абазинский': 'абазинский', 'абаза бызшва': 'абазинский'} (и другие подобные пары "ключ-значение" для всех имеющихся языков)
    result = {}
    for __, value in values.items():
        name = value["Язык:"]
        name_low = name.lower()
        selfname = value["Самоназвание:"]

        if ', ' in selfname:
            selfname = selfname.replace(', ', '\n')
        if selfname == 'tatarça татарча':
            selfname = selfname.replace(' ', '\n')
        if '/' in selfname:
            selfname = selfname.replace('/', '\n')
        if ';' in selfname:
            selfname = selfname.replace('; ', '\n')

        result[name_low] = name_low

        selfname = selfname.split('\n')
        for s in selfname:
            result[s] = name_low

    return result

@bot.message_handler(commands=['start'])
def send_welcome(message):
    path = './langs'
    file_count = len([name for name in os.listdir(path) if os.path.isfile(os.path.join(path, name))])

    bot.send_message(message.chat.id, 'Здравствуйте! Это бот, который может рассказать некоторую информацию о любом из языков России.\n\n\
Пожалуйста, введите название или самоназвание (или какую-либо их часть) \
интересующего вас языка. \n\nСейчас в моей базе данных содержится информация о ' + str(file_count) + ' языках. Для просмотра их списка введите /langs.\n\nВ случае затруднения воспользуйтесь командой /help.')

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, 'Чтобы начать использование бота, вам нужно лишь отправить ему команду /start, \
а затем \u2013 название/самоназвание (или их часть, например, для южноалтайского языка можно написать лишь "алт") интересующего вас языка, \
а бот, в свою очередь, расскажет все, что знает об этом языке, \
а также распечатает список языков, названия или самоназвания которых хотя бы частично совпадают с вашим запросом.\n\n\
Для просмотра полного списка языков воспользуйтесь командой /langs.')

@bot.message_handler(commands=['langs'])
def langs_list(message):
    chat_id = message.chat.id
    v = lang_page()
    r = make_dict(v)
    langs_set = set(lang for lang in sorted(r.values()))

    bot.send_message(chat_id, 'Доступные языки: ' + ', '.join(sorted(langs_set)) + '.')

@bot.message_handler(func=lambda m: True)
def send_info(message): # эта функция получает на вход сообщение пользователя, преобразует его (переводит в нижний регистр и удаляет лишние слова)
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')
    bot.send_sticker(chat_id, 'CAADAgADiQADhC64BjZ1mCglHfVbAg')
    v = lang_page()
    r = make_dict(v)
    message_text = message.text.lower()
    message_text = "".join(message_text.split()) # удаление пробелов

    if 'язык' in message_text:
        clean_message = message_text.replace('язык', '')
    else:
        clean_message = message_text

    a = [value for key, value in r.items() if key.find(clean_message) != -1]
    try:
        lang = a[0]
    except:
        try:
            lang = r[clean_message]
        except:
            lang = ""

    if lang is not "":
        result = ""
        for k in v:
            if lang in v[k]["Язык:"]:
                if v[k]["Самоназвание:"] is not "":
                    selfn = ' (' + v[k]["Самоназвание:"] + ')'
                else:
                    selfn = ''

                result += 'Вот, что мне удалось найти про ' + lang + selfn + ':\n\n'

                values_copy = dict(v[k])
                del values_copy["Язык:"]
                del values_copy["Самоназвание:"]
                for x, y in values_copy.items():
                    if y is not "":
                        result += x + ' ' + y + '\n'
                break

        bot.send_message(chat_id, result)

        others = set(a)
        if len(others) > 1:
            others.remove(lang)
            bot.send_message(chat_id, 'Другие языки по вашему запросу: ' + ", ".join(others))
    else:
        bot.send_message(chat_id, 'К сожалению, в моей базе данных отсутствует информация об этом языке :(\nМожет быть, вы попробуете ввести другой запрос?')

@app.route("/bot", methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

if __name__ == '__main__':
    import os
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
