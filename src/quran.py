"""
Date: 17 Februari 2021
"""

from bs4 import BeautifulSoup
from requests import get
import re
from pprint import pprint


class Quran:

    __URL = 'https://litequran.net'

    def __init__(self):
        self._response = {
                'data'  : []
            }

    def daftar_surah(self):
        del self._response['data'][0:] # hapus isi data jika ada
        resp = get(self.__URL).text
        pars = BeautifulSoup(resp, 'html.parser')

        ol = pars.find('ol', {'class':'list'})
        daftar = ol.find_all('a')
        for a in daftar:
            nama_surah = a.string
            self._response['data'].append(nama_surah)
        return self._response

    def surah(self, surah, ayat=None):
        del self._response['data'][0:] # hapus isi data jika ada
        resp = get(self.__URL+'/'+surah.lower()).text
        pars = BeautifulSoup(resp, 'html.parser')

        ol  = pars.find('ol')
        if ol is not None:
            li = ol.find_all('li')
        else:
            self._response['error']   = True
            self._response['message'] = "surah tidak ditemukan"
            self._response['surah']   = surah
            return self._response

        for data in li:
            if ayat is not None and type(ayat) is int:
                if len(li) >= ayat:
                    if li.index(data) == ayat-1:
                        arabic = data.find('span', {'class':'ayat'}).string
                        bacaan = data.find('span', {'class':'bacaan'}).string
                        arti   = data.find('span', {'class':'arti'}).string
                        self._response['error']   = False
                        self._response['data'].append(dict(arabic=arabic, bacaan=bacaan, arti=arti))
                        break
                else:
                    self._response['error'] = True
                    self._response['message'] = "ayat tidak ditemukan"
                    self._response['surah'] = surah
                    self._response['number_of_verses'] = len(li)
                    self._response['verse_requests'] = ayat
                    break
            else:
                arabic = data.find('span', {'class':'ayat'}).string
                bacaan = data.find('span', {'class':'bacaan'}).string
                arti   = data.find('span', {'class':'arti'}).string

                self._response['error']   = False
                self._response['data'].append(dict(arabic=arabic, bacaan=bacaan, arti=arti))
        return self._response


if __name__ == '__main__':
    quran = Quran()
    m = quran.surah('al-fatihah')
    pprint(m)
