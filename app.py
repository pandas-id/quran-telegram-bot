"""
Date: 24 Februari 2021
Last Update: 1 Oktober 2022
"""

from telepot import Bot, exception, message_identifier
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
from src.quran import Quran
from pprint import pprint
import os
import json


# inisialisasi
token   = os.environ['TOKEN'] # ganti nilai varibel dengan token bot Anda
bot     = Bot(token)

web   = Flask(__name__)
HOST = 'https://quran-telegram-bot.herokuapp.com/'

class App:

    def __init__(self):
        self.__chat_id = None
        self.__username = None
        self.__quran = Quran()
        # self.__quran_id = json.loads(quran_data)
        self.__chapters_data = self.__quran.chapters_data()

        # konfigurasi
        self._terjemahan = True
        self._bacaan = True

        # inisialisasi varibel untuk penanganan perintah surah
        self._chapter = None
        self._index = 0
        self._pages_data = []
        self._messages = []
        self._identifier = None

    # main handler{{{
    def main_handler(self, msg):
        self.__chat_id  = msg['message']['chat']['id']
        self.__username = msg['message']['chat']['first_name']
        message_id = msg['message']['message_id']
        command         = msg['message']['text']

        if command[0] == '/':
            if command == '/start':
                self.__handling_start_command()
        else:
            self.__send_script_of_chapter(command)

        # }}}

    # handind start command{{{
    def __handling_start_command(self):
        mess = f'Assalamualaikum <b>{self.__username}</b>, selamat datang di Al-Quran Bot.'
        bot.sendMessage(self.__chat_id, mess, parse_mode='html')

        # send keyboard button
        chapter_names = list(self.__chapters_data.keys())
        keyboard = []
        while len(chapter_names) != 0:
            for _ in range(1):
                keyboard.append([
                    KeyboardButton(text=chapter_names[0]),
                    KeyboardButton(text=chapter_names[1])
                ])
            del chapter_names[0:2]

        keyboard = ReplyKeyboardMarkup(keyboard=keyboard)

        bot.sendMessage(self.__chat_id, 'Silahakan pilihi nama surah yang ingin Anda baca.', reply_markup=keyboard)#}}}

    def __send_script_of_chapter(self, chapter):
        self._chapter = chapter
        r = self.__create_page()
        if r:
            self.__generate_message()
            markup = self.__create_reply_markup()
            self._identifier = bot.sendMessage(self.__chat_id, self._messages[self._index], reply_markup=markup)

    # reply markup{{{
    def __create_reply_markup(self):
        terjemahan = 'ON' if self._terjemahan else 'OFF'
        bacaan = 'ON' if self._bacaan else 'OFF'

        markup = InlineKeyboardMarkup(inline_keyboard=[
            [ InlineKeyboardButton(
                text='«',
                callback_data='prev-page'),
            InlineKeyboardButton(
                text=f'{self._index+1} / {len(self._pages_data)}',
                callback_data='page'),
            InlineKeyboardButton(
                text='»',
                callback_data='next-page')],

            [ InlineKeyboardButton(
                text="Terjemahan: {}".format(terjemahan),
                callback_data="terjemahan"),
            InlineKeyboardButton(
                text="Bacaan: {}".format(bacaan),
                callback_data="bacaan")]
        ])
        return markup# }}}


    # create page{{{
    def __create_page(self, ayat=None):
        verses = self.__quran.verses_of_chapter(chapter=self.__chapters_data[self._chapter], verse_id=ayat)

        if verses.get('error'):
            if verses['error']['message'] == 'chapter not found':
                mess = f"Surah *{verses['surah']}* tidak ditemukan.Coba lihat /daftarsurah."
            elif verses['message'] == 'verse not found':
                mess = f"Ayat ke-*{verses['verse_requests']}* pada surah *{verses['surah']}* tidak tersedia.Surah *{verses['surah']}* hanya terdiri atas *{verses['number_of_verses']}* ayat."

            bot.sendMessage(self.__chat_id, mess, parse_mode='Markdown')
            return False
        else:
            self._pages_data = [] # kosongkan varibel
            self._index = 0 # kembalikan index
            mess  = ''
            page = []
            for id in verses:
                lenms = len(verses[id]['arabic']) + len(verses[id]['translate']) + len(verses[id]['meaning'])

                if lenms > 2000:
                    if len(page) != 0:
                        self._pages_data.append(page)
                        page = []

                    page.append(verses[id])
                    self._pages_data.append(page)
                    page = []
                    mess = ''
                elif len(mess) > 2000:
                    self._pages_data.append(page)
                    mess = ''
                    page = []

                mess += verses[id]['arabic'] + verses[id]['translate'] + verses[id]['meaning']
                page.append(verses[id])

            self._pages_data.append(page)
            return True# }}}

    # generate message{{{
    def __generate_message(self):
        del self._messages[0:] # hapus isi list
        mess = ''
        for page in self._pages_data:
            for data in page:
                mess += data['arabic']
                if self._bacaan:
                    mess += '\n\n' + data['translate']
                if self._terjemahan:
                    mess += '\n\n' + data['meaning']

                mess += '\n\n\n'
            self._messages.append(mess)
            mess = ''# }}}

    # handling of page{{{
    def __handling_of_page(self, data, query_id):
        if data == 'next-page':
            if len(self._messages)-1 != self._index:
                self._index += 1
                markup       = self.__create_reply_markup()

                bot.editMessageText(message_identifier(self._identifier), self._messages[self._index], reply_markup=markup)
            else:
                bot.answerCallbackQuery(query_id, text="Ini halaman terakhir")
        elif data == 'prev-page':
            if self._index != 0:
                self._index -= 1

                markup       = self.__create_reply_markup()

                bot.editMessageText(message_identifier(self._identifier), self._messages[self._index], reply_markup=markup)
            else:
                bot.answerCallbackQuery(query_id, text="Ini halaman pertama")# }}}

    # handling of configuration{{{
    def __handling_of_configuration(self, data):
        if data == 'terjemahan':
            self._terjemahan = False if self._terjemahan else True
        elif data == 'bacaan':
            self._bacaan = False if self._bacaan else True

        self.__generate_message()
        markup = self.__create_reply_markup()
        bot.editMessageText(message_identifier(self._identifier), self._messages[self._index], reply_markup=markup)# }}}

    # main markup handler{{{
    def main_markup_handler(self, msg):
        data = msg['callback_query']['data']
        query_id = msg['callback_query']['id']

        if data == 'next-page' or data == 'prev-page':
            self.__handling_of_page(data, query_id)
        elif data == 'terjemahan' or data == 'bacaan':
            self.__handling_of_configuration(data)# }}}

app = App()

@web.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        new_msg = request.get_json()
        if 'message' in str(new_msg):
            if new_msg.get('message'):
                app.main_handler(new_msg)
            elif new_msg.get('callback_query'):
                app.main_markup_handler(new_msg)

    return 'OK'


if __name__ == '__main__':
    try:
        bot.setWebhook(HOST)
    except exception.TooManyRequestsError:
        pass
    # start
    web.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
