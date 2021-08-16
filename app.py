"""
Date: 24 Februari 2021
"""

from telepot import Bot, exception, message_identifier
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from src.quran import Quran
from pprint import pprint
import os


# inisialisasi
token   = '1603495571:AAHl0H8oVK1ciPhndClLxUbu1jFALCbG7bc'
bot     = Bot(token)

web   = Flask(__name__)
HOST = 'https://quran-telegram-bot.herokuapp.com'


class App:

    def __init__(self):
        self.__chat_id = None
        self.__username = None
        self.__quran = Quran()

        # konfigurasi
        self._terjemahan = True
        self._bacaan = True

        # inisialisasi varibel untuk penanganan perintah surah
        self._surah = None
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

        if command == '/start':
            self.__handling_start_command()
        elif command == '/help':
            self.__handling_help_command()
        elif command == '/daftarsurah':
            self.__handling_daftarsurah_command()
        elif '/surah' in command:
            self.__handling_surah_command(cmd=command)
        elif '/quran' in command:
            self.__handling_quran_command(command, message_id)# }}}

    # handind start command{{{
    def __handling_start_command(self):
        mess = f'Assalamualaikum <b>{self.__username}</b>, selamat datang di Al-Quran Bot.'
        bot.sendMessage(self.__chat_id, mess, parse_mode='html')
        self.__handling_help_command()# }}}

    # handling help command{{{
    def __handling_help_command(self):
        mess = f'''
Beberapa perintah yang dapat Anda gunakan:


/daftarsurah - lihat semua surah di Al-Quran

<b>Surah</b>
/surah [ <u>nama surah</u> ]
<i>contoh</i>
/surah al-falaq - lihat surah Al-Falaq

<b>Quran</b>
/quran [ <u>nama surah</u> ] [ <u>ayat</u> ]
<i>contoh</i>
/quran al-fatihah 3 - lihat surah Al-Fatihah ayat ke-3


~ @PandasID
        '''
        bot.sendMessage(self.__chat_id, mess, parse_mode='html')# }}}

    # handing daftarsurah command{{{
    def __handling_daftarsurah_command(self):
        mess = ''
        daftar_surah = self.__quran.daftar_surah()['data']
        for data in daftar_surah:
            mess += str((daftar_surah.index(data)+1)) + '. ' + data + '\n'
        bot.sendMessage(self.__chat_id, mess)# }}}

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

    # handling surah command{{{
    def __handling_surah_command(self, cmd):
        cmds = cmd.split(' ')

        if len(cmds) > 1:
            self._surah = cmds[1]
            r = self.__create_page() # buat halaman
            if r:
                self.__generate_message()
                markup = self.__create_reply_markup()
                self._identifier = bot.sendMessage(self.__chat_id, self._messages[self._index], reply_markup=markup)
        else:
            mess = """
<b>Surah</b>
/surah [ <u>nama surah</u> ]
<i>contoh</i>
/surah al-falaq - lihat surah Al-Falaq
"""
            bot.sendMessage(self.__chat_id, mess, parse_mode='html')#}}}

    # create page{{{
    def __create_page(self, ayat=None):
        resp  = self.__quran.surah(surah=self._surah, ayat=ayat)

        if resp.get('error'):
            if resp['message'] == 'surah tidak ditemukan':
                mess = f"Surah *{resp['surah']}* tidak ditemukan.Coba lihat /daftarsurah."
            elif resp['message'] == 'ayat tidak ditemukan':
                mess = f"Ayat ke-*{resp['verse_requests']}* pada surah *{resp['surah']}* tidak tersedia.Surah *{resp['surah']}* hanya terdiri atas *{resp['number_of_verses']}* ayat."

            bot.sendMessage(self.__chat_id, mess, parse_mode='Markdown')
            return False
        else:
            self._pages_data = [] # kosongkan varibel
            self._index = 0 # kembalikan index
            mess  = ''
            page = []
            for data in resp['data']:
                lenms = len(data['arabic']) + len(data['bacaan']) + len(data['arti'])

                if lenms > 2000:
                    if len(page) != 0:
                        self._pages_data.append(page)
                        page = []

                    page.append(data)
                    self._pages_data.append(page)
                    page = []
                    mess = ''
                elif len(mess) > 2000:
                    self._pages_data.append(page)
                    mess = ''
                    page = []

                mess += data['arabic'] + data['bacaan'] + data['arti']
                page.append(data)

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
                    mess += '\n\n' + data['bacaan']
                if self._terjemahan:
                    mess += '\n\n' + data['arti']

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

    # handling quran command{{{
    def __handling_quran_command(self, cmd, mess_id):
        cmds = cmd.split(' ')

        if len(cmds) > 2 and len(cmds) == 3:
            self._surah = cmds[1]
            ayat = cmds[2]

            if ayat.isdecimal():
                r = self.__create_page(ayat=int(ayat))
                if r:
                    self.__generate_message()
                    bot.sendMessage(self.__chat_id, self._messages[0], reply_to_message_id=mess_id)
        else:
            mess = """
<b>Quran</b>
/quran [ <u>nama surah</u> ] [ <u>ayat</u> ]
<i>contoh</i>
/quran al-fatihah 3 - lihat surah Al-Fatihah ayat ke-3
"""
            bot.sendMessage(self.__chat_id, mess, parse_mode='html')# }}}

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
    except telepot.exception.TooManyRequestsError:
        pass
    # start
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
