#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*

import re

from html2tei import parse_date, BASIC_LINK_ATTRS, decompose_listed_subtrees_and_mark_media_descendants, tei_defaultdict

PORTAL_URL_PREFIX = 'https://hvg.hu/'

ARTICLE_ROOT_PARAMS_SPEC = [(('div',), {'class': 'article-main'})]

HTML_BASICS = {'p', 'h3', 'h2', 'h4', 'h5', 'em', 'i', 'b', 'strong', 'mark', 'u', 'sub', 'sup', 'del', 'strike',
               'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'quote', 'figure', 'iframe', 'script', 'noscript'}

SOURCE = ['hvg.hu', 'MTI', 'MTI/hvg.hu', 'MTI / hvg.hu', 'Marabu', 'HVG', 'Eduline', 'Reuters', 'honvedelem.hu', 'BBC',
          'Euronews', 'EUrologus', 'OS', 'Dow Jones', 'DPA', 'DW', 'Hszinhua', 'MTA', 'AP', 'AFP', 'HVG Konferencia',
          'Zgut Edit', 'Index', 'foodnetwork', 'mult-kor.hu', 'MT Zrt.', 'élelmiszer online', 'atlatszo.blog.hu',
          'Blikk', 'HVG Extra Business', 'Origo', 'Bors', '- esel -', 'Magyar Nemzet', 'EFE', 'merites.hu',
          'Népszabadság', 'Inforádió', 'HVG Extra Pszichológia', 'MTI-OS', 'MLF', 'ITAR-TASZSZ', 'MNO',
          'MR1-Kossuth Rádió', 'HavariaPress', 'CNN', 'Bank360.hu', 'Bankmonitor.hu', 'ingatlanmenedzser.hu']


def get_meta_from_articles_spec(tei_logger, url, bs):
    data = tei_defaultdict()
    data['sch:url'] = url
    article_root = bs.find('div', class_='article-content')
    if article_root is not None:
        date_tag = bs.find('time', class_='article-datetime')
        if date_tag is not None and 'datetime' in date_tag.attrs.keys():
            parsed_date = parse_date(date_tag.attrs['datetime'][:19], '%Y-%m-%dT%H:%M:%S')
            data['sch:datePublished'] = parsed_date
        else:
            tei_logger.log('WARNING', f'{url}: DATE TAG NOT FOUND!')
        modified_date_tag = bs.find('time', class_='lastdate')
        if modified_date_tag is not None and 'datetime' in modified_date_tag.attrs.keys():
            parsed_modified_date = parse_date(modified_date_tag.attrs['datetime'][:19], '%Y-%m-%dT%H:%M:%S')
            data['sch:datePublished'] = parsed_modified_date
        else:
            tei_logger.log('DEBUG', f'{url}: MODIFIED DATE TAG NOT FOUND!')
        title = article_root.find('div', class_='article-title article-title')
        if title is not None:
            article_title = title.find('h1')
            data['sch:name'] = article_title.text.strip()
        else:
            tei_logger.log('WARNING', f'{url}: TITLE TAG NOT FOUND!')
        author_or_source_tag = article_root.find('div', class_='author-name')
        if author_or_source_tag is not None:
            author_or_source = author_or_source_tag.text.strip().\
                replace('\r', '').replace('\n', '').replace('\t', '').replace('Követés', '')
            if author_or_source in SOURCE:
                data['sch:source'] = author_or_source
            else:
                data['sch:author'] = author_or_source
        else:
            tei_logger.log('WARNING', f'{url}: AUTHOR / SOURCE TAG NOT FOUND!')
        keywords_root = article_root.find('div', class_='article-tags')
        if keywords_root is not None:
            keywords_list = [t.text.strip() for t in keywords_root.find_all('a') if t is not None]
            data['sch:keywords'] = keywords_list
        else:
            tei_logger.log('DEBUG', f'{url}: TAGS NOT FOUND!')
        info_root = bs.find('div', class_='info')
        if info_root is not None:
            section_main = info_root.find('a')
            if section_main is not None:
                data['sch:articleSection'] = section_main.text.strip()
            else:
                tei_logger.log('WARNING', f'{url}: SECTION TAG NOT FOUND!')
        return data
    else:
        tei_logger.log('WARNING', f'{url}: ARTICLE BODY NOT FOUND!')
        return None


def excluded_tags_spec(tag):
    if tag.name not in HTML_BASICS:
        tag.name = 'else'
    tag.attrs = {}
    return tag


BLOCK_RULES_SPEC = {}
BIGRAM_RULES_SPEC = {}
LINKS_SPEC = BASIC_LINK_ATTRS
DECOMP = [(('script',), {}),
          (('div',), {'class': 'placeholder-ad'}),
          (('div',), {'class': 'article-series-box'})
          ]
LINK_FILTER_SUBSTRINGS_SPEC = re.compile('|'.join(['LINK_FILTER_DUMMY_STRING']))
MEDIA_LIST = []


def decompose_spec(article_dec):
    decompose_listed_subtrees_and_mark_media_descendants(article_dec, DECOMP, MEDIA_LIST)
    return article_dec


BLACKLIST_SPEC = [
    # HVG 360 articles:
    'https://hvg.hu/360/20210704_Hatvanpuszta_major_orban_Viktor_orban_Gyozo',
    'https://hvg.hu/360/20200217_Orbanertekeles_2020',
    'https://hvg.hu/360/20190619_Koszeg_Ferenc_velemeny',
    # Empty articles:
    'https://hvg.hu/kkv/20171107_rudi_kviz_pottyos_turos',
    'https://hvg.hu/gazdasag/20181109_Ujra_eladta_a_sirkoves_a_temetokbol_lopott_vazakat',
    'https://hvg.hu/itthon/20130212_Havazas_20130212',
    'https://hvg.hu/hvgkonyvek/20191119_Az_ertekesites_titkos_kodja__avagy_mi_kulonbozteti_meg_a_gyozteseket',
    'https://hvg.hu/gazdasag/20180629_Harom_miniszter_is_elment_Szegedre_egy_fektelep_atadasara',
    'https://hvg.hu/gazdasag/20200511_uzemanyag_benzin_gazolaj',
    'https://hvg.hu/elet/20190330_On_melyik_idoszamitast_tartana_meg_Szavazzon',
    'https://hvg.hu/elet/20170804_Csobbanak_es_dinnyeznek_a_jegesmedvek_az_Allatkertben',
    'https://hvg.hu/sport/20130201_Uj_Ferrari',
    'https://hvg.hu/hvgkonyvek/20200105_Eric_Idle_Monty_Python_konyv',
    'https://hvg.hu/plazs/20160401_Hosszu_Katinka_kopasz',
    'https://hvg.hu/vilag/20160510_Dronfelvetelrol_is_megnezheti_a_gyozelem_napi_moszkvai_tuzijatekot',
    'https://hvg.hu/vilag/20170924_Macron_partjanak_nem_sikerult_az_attores_a_szenatusban',
    'https://hvg.hu/sport/20180325_Forma1_Vettel_nyerte_az_idenynyitot',
    'https://hvg.hu/elet/20200509_Csak_ugy_potyognak_az_elefantbebik_a_pragai_allatkertben',
    'https://hvg.hu/vilag/20130215_Oroszorszag_meteor',
]


MULTIPAGE_URL_END = re.compile(r'^\b$')  # Dummy


def next_page_of_article_spec(_):
    return None