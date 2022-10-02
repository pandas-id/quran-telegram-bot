"""
Date: 17 Februari 2021
Last Update: 2 Oktober 2022
"""

from bs4 import BeautifulSoup
from requests import get

class Quran:

    __URL = 'https://litequran.net/'

    def __init__(self):
        self._response = {
                'data'  : []
            }

    def chapters_data(self):
        data = {}

        resp = get(self.__URL).text
        pars = BeautifulSoup(resp, 'html.parser')

        ol = pars.find('ol', {'class':'list'})
        lists = ol.find_all('a')
        for list in lists:
            chapter_name = list.string
            data[chapter_name] = list['href']

        return data

    def verses_of_chapter(self, chapter, verse_id=None ):
        verses_data = {}
        resp = get(self.__URL+chapter)

        if resp.status_code == 200:
            pars = BeautifulSoup(resp.text, 'html.parser')
        elif resp.status_code == 404:
            self._response['error'] = {'message': 'chapter not found'}
            return self._response

        ol  = pars.find('ol')

        id = 1
        for verse_html in ol.find_all('li'):
            arabic = verse_html.find('p', {'class':'arabic'}).text
            translate = verse_html.find('p', {'class':'translate'}).text
            meaning   = verse_html.find('p', {'class':'meaning'}).text

            verses_data[id] = dict(arabic=arabic, translate=translate, meaning=meaning)
            # verses_data.append(, id=id))
            id += 1

        if verse_id is not None and type(verse_id) is int:
            if verse_id > len(verses_data):
                self._response['error'] = {
                    'message': 'verse not found',
                    'number_of_verses': len(verses_data)
                }
                return self._response
            else:
                return verses_data[verse_id]

        return verses_data
