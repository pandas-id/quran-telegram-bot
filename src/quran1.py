"""
Date: 16 Februari 2021
Deskripsi: Scrapping dari https://m.merdeka.com/quran
"""

from bs4 import BeautifulSoup
from requests import get
import re
from pprint import pprint


class Quran:

    __URL = 'https://m.merdeka.com/quran'

    def __init__(self):
        self._response = {
                'error' : None,
                'data'  : []
            }

    def daftar_surah(self):
        resp = get(self.__URL).text
        pars = BeautifulSoup(resp, 'html.parser')

        ul = pars.find('ul', {'class':'quran_surat'})
        a = ul.find_all('a')
        for data in a:
            nama_surah = data.find('p').string
            # surahke = re.search(r'\d\d\d|\d\d|\d', nama_surah)
            # nama_surah = re.sub('\d', '', nama_surah)[2:] # hilangkan angka
            terjemahan = data.find('span').string
            self._response['data'].append(dict(surah=nama_surah, terjemahan=terjemahan))
        return self._response

    def surah(self, surah, ayat=None):
        resp = get(self.__URL+'/'+surah.lower()).text
        pars = BeautifulSoup(resp, 'html.parser')

        ayat_page  = pars.find('ul', {'class':'ayat_page'})
        if ayat_page is not None:
            quran_list = ayat_page.find_all('li', {'class':'quran_list'})
        else:
            self._response['error'] = True
            self._response['pesan'] = f"Surah {surah} tidak ditemukan."
            return self._response

        for data in quran_list:
            if ayat is not None and type(ayat) is int:
                if len(quran_list) > ayat:
                    if quran_list.index(data) == ayat-1:
                        arabic     = data.find('p', {'class':'arabic'}).string
                        terjemahan = data.find('p', {'class':'terjemahan'}).string
                        self._response['data'].append(dict(arabic=arabic[::-1], terjemahan=terjemahan))
                        break
                else:
                    self._response['error'] = True
                    self._response['pesan'] = f"Ayat ke-{ayat} pada surah {surah} tidak ditemukan.Surah {surah} hanya berjumlah {len(quran_list)} ayat"
                    break
            else:
                arabic     = data.find('p', {'class':'arabic'}).string
                terjemahan = data.find('p', {'class':'terjemahan'}).string
                self._response['error'] = False
                self._response['data'].append(dict(arabic=arabic, terjemahan=terjemahan))
        return self._response


if __name__ == '__main__':
    quran = Quran()
    pprint(quran.surah('al-falaq'))
