import json
import re

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from mtgsdk import Card
from mtgsdk import Set


SCRYFALL_URI = 'https://svgs.scryfall.io/card-symbols/'
SCRYFALL_SETS = 'https://api.scryfall.com/sets/'


def get_sets() -> list[dict]:
    res = requests.get(SCRYFALL_SETS)
    data = res.json()
    # print(data)
    return data['data']


def get_symbol_uri(symbol: str) -> str:
    return f'{SCRYFALL_URI}{symbol}.svg'


def get_card_symbols() -> dict:
    data = {}
    response = requests.get('https://api.scryfall.com/symbology')
    if response.status_code == 200:
        data = response.json()
    # print(data)
    return data


def process_symbol_str(symbols: str) -> tuple:
    symb_list = tuple(str(symbols).replace('{', '').replace('}', ''))
    # for symb in symb_list:
    #     image_url =
    return symb_list


# @cache_page(60 * 15)
def home(request):
    try:
        card_sets = get_sets()
        cards = [
            dict(
                code=data['code'],
                symbol_url=data['icon_svg_uri'],
                name=data['name'],
                release_date=data['released_at']
            ) for data in card_sets
        ]
        print(cards)
        return render(request, 'card_sets.html', {'sets': cards})
    except Exception as e:
        return JsonResponse({'Error': str(e)})


@cache_page(60 * 15)
def card_list(request, set_id: str):
    card_set = Set.find(set_id)
    rs = Card.where(set=set_id).all()
    cards = [
        {
            'name': r.name,
            'og_mana_cost': r.mana_cost,
            'mana_cost': process_symbol_str(r.mana_cost),
            'color_identity': r.color_identity,
            'colors': r.colors,
            'id': r.id,
            'type': r.type,
            'subtypes': r.subtypes,
            'text': r.text,
            'image_url': r.image_url,
            'power': r.power,
            'toughness': r.toughness
        }
        for r in rs
    ]
    context = {'cards': cards, 'title': 'Card List', 'card_set': card_set}
    return render(request, 'cards.html', context)


def card_image(request, card_id: str):
    obj = Card.find(card_id)
    card_set = Set.find(obj.set)
    o_text = obj.text
    symbols = re.findall(r'\{.*?}', o_text)
    for symbol in symbols:
        img_url = f'https://svgs.scryfall.io/card-symbols/{str(symbol).strip("{}")}.svg'
        print(img_url)
    print(o_text)
    context = {'title': 'Card Image', 'obj': obj, 'card_set': card_set}
    return render(request, 'card_image.html', context)
