"""
Date: 16 Februari 2021
"""

from telepot import Bot, loop, glance, exception
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
import telepot
from flask import Flask, request
from src.quran import Quran
import os



# inisialisasi
token   = os.environ['TOKEN']
bot     = Bot(token)

quran = Quran()
app   = Flask(__name__)
HOST = 'https://quran-telegram-bot.herokuapp.com'

def user_command(msg):
    return msg['text']


def handling_start_command(chat_id, username):
    mess = f'''
Assalamualaikum {username}, selamat datang di Al-Quran Bot.
    '''
    bot.sendMessage(chat_id, mess)
    handling_help_command(chat_id)


def handling_help_command(chat_id):
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
    bot.sendMessage(chat_id, mess, parse_mode='html')


def handling_daftarsurah_command(chat_id):
    mess = ''
    daftar_surah = quran.daftar_surah()['data']
    for data in daftar_surah:
        mess += str((daftar_surah.index(data)+1)) + '. ' + data + '\n'
    bot.sendMessage(chat_id, mess)


mess = None
sent = None
ind = 0

# handing surah command

def create_reply_markup():
    global ind
    global mess
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [ InlineKeyboardButton(
            text="Prev",
            callback_data='prev'),
        InlineKeyboardButton(
            text=f"Page {ind+1} of {len(mess)}",
            callback_data='data'),
        InlineKeyboardButton(
            text='Next',
            callback_data='next')
        ]
    ])
    return markup

def handling_surah_command(chat_id, msg_id, comm=None, query_id=None, callback_data=None):
    global mess
    global ind
    global sent
    if comm is not None:
        comm = comm.split(' ')
        if len(comm) > 1:
            surah  = comm[1]
            mess   = create_surah_message(surah)
            ind    = 0 # reset index
            markup = create_reply_markup()
            if type(mess) == list:
                sent = bot.sendMessage(chat_id, mess[ind], reply_markup=markup)
            else:
                bot.sendMessage(chat_id, mess, parse_mode='html')
    else:
        if callback_data == 'next':
            if len(mess)-1 != ind:
                ind += 1
                markup = create_reply_markup()
                bot.editMessageText(telepot.message_identifier(sent), mess[ind], reply_markup=markup)
            else:
                bot.answerCallbackQuery(query_id, text="Ini halaman terakhir")
        elif callback_data == 'prev':
            if ind != 0:
                ind -= 1
                markup = create_reply_markup()
                bot.editMessageText(telepot.message_identifier(sent), mess[ind], reply_markup=markup)
            else:
                bot.answerCallbackQuery(query_id, text="Ini halaman pertama")


def create_surah_message(surah):
    resp = quran.surah(surah)

    page = []
    if not resp.get('error'):
        mess = ''

        for data in resp['data']:
            if len(mess) < 3000:
                mess += data['arabic'] + '\n' + data['arti'] + '\n\n\n'
            else:
                mess += data['arabic'] + '\n' + data['arti'] + '\n\n\n'
                page.append(mess)
                mess = ''
        page.append(mess)
    else:
        mess = f'Surah <b>{surah}</b> tidak ditemukan. Coba lihat /daftarsurah .'
        return mess

    return page


# handing quran command
def handling_quran_command(chat_id, mess_id, comm):
    comm = comm.split(' ')

    if len(comm) > 2:
        surah = comm[1]
        ayat  = comm[2] if comm[2].isdecimal() else None

        if ayat is not None:
            resp = quran.surah(surah, ayat=int(ayat))
            if not resp.get('error'):
                mess = '*'+resp['data'][0]['arabic']+'*' + '\n' + resp['data'][0]['arti']
            else:
                mess = resp['pesan']
            bot.sendMessage(chat_id, mess, reply_to_message_id=mess_id, parse_mode='Markdown')
            return True
        else:
            mess = """
/quran [ <u>nama surah</u> ] [ <u>ayat</u> ]
<i>contoh</i>
/quran al-fatihah 3 - lihat surah Al-Fatihah ayat ke-3"""
    else:
        mess = """
/quran [ <u>nama surah</u> ] [ <u>ayat</u> ]
<i>contoh</i>
/quran al-fatihah 3 - lihat surah Al-Fatihah ayat ke-3"""
    bot.sendMessage(chat_id, mess, reply_to_message_id=mess_id, parse_mode='html')


def main_markup_handler(msg):
    data     = msg['callback_query']['data']
    chat_id  = msg['callback_query']['message']['chat']['id']
    mess_id  = msg['callback_query']['message']['message_id']
    query_id = msg['callback_query']['id']

    if data == 'next' or data == 'prev':
        handling_surah_command(chat_id, mess_id, query_id=query_id, callback_data=data)


def main_handler(msg):
    chat_id = msg['message']['chat']['id']

    command = msg['message'].get('text')
    # perintah dasar
    if command == '/start':
        handling_start_command(chat_id, msg['message']['chat']['first_name'])
    elif command == '/help':
        handling_help_command(chat_id)
    # perintah lanjut
    elif command == '/daftarsurah':
        handling_daftarsurah_command(chat_id)
    elif '/surah' in command:
        handling_surah_command(chat_id, msg['message']['message_id'], comm=command)
    elif '/quran' in command:
        handling_quran_command(chat_id, msg['message']['message_id'], command)


# webhook = loop.OrderedWebhook(bot, main_handler)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        new_msg = request.get_json()
        if 'message' in str(new_msg):
            if new_msg.get('message'):
                main_handler(new_msg)
            elif new_msg.get('callback_query'):
                main_markup_handler(new_msg)
        return 'OK'
    else:
        return 'OK'

if __name__ == '__main__':

    try:
        bot.setWebhook(HOST)
    except telepot.exception.TooManyRequestsError:
        pass
    # start
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
