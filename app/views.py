import json
import re

import requests
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from mtgsdk import Card
from mtgsdk import Set

from app.forms import SearchForm

SCRYFALL_API = 'https://api.scryfall.com/'
SCRYFALL_SETS = SCRYFALL_API + 'sets/'
SCRYFALL_SYMBOLS = SCRYFALL_API + 'symbology/'
SCRYFALL_URI = 'https://svgs.scryfall.io/card-symbols/'


def customhandler404(request, exception, template_name='404.html'):
    response = render(request, template_name)
    response.status_code = 404
    return response


def get_sets() -> list[dict]:
    res = requests.get(SCRYFALL_SETS)
    data = res.json()
    # print(data)
    return data['data']


def get_symbol_uri(symbol: str) -> str:
    return f'https://svgs.scryfall.io/card-symbols/{str(symbol).strip("{}")}.svg'


def convert_symbols(text: str) -> str:
    symbols = re.findall(r'\{.*?}', text)
    if len(symbols) > 0:
        for symbol in symbols:
            symbol_img = f'<img class="mana-image-sm" src="{get_symbol_uri(symbol)}" alt="">'
            text = str(text).replace(symbol, symbol_img)
    return text


@cache_page(60 * 15)
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
        return render(request, 'app/card_sets.html', {'sets': cards})
    except Exception as e:
        return JsonResponse({'Error': str(e)})


@cache_page(60 * 15)
def card_list(request, set_id: str):
    try:
        card_set = Set.find(set_id)
        rs = Card.where(set=set_id).all()
        # print(rs)
        cards = [
            {
                'name': r.name,
                'og_mana_cost': r.mana_cost,
                'mana_cost': r.mana_cost,
                'color_identity': r.color_identity,
                'colors': r.colors,
                'id': r.id,
                'type': r.type,
                'subtypes': r.subtypes,
                'text': convert_symbols(r.text) if r.text else '',
                'image_url': r.image_url,
                'power': r.power,
                'toughness': r.toughness
            }
            for r in rs
        ]

        context = {
            'cards': cards,
            'title': card_set.name,
            'card_set': card_set
        }
        return render(request, 'app/cards.html', context)
    except TypeError as e:
        return JsonResponse({'TypeError': str(e)})
    except Exception as e:
        return JsonResponse({'Error': str(e)})


@cache_page(60 * 15)
def card_image(request, card_id: str):
    try:
        obj = Card.find(card_id)
        card_set = Set.find(obj.set)
        o_text = convert_symbols(obj.text)
        o_card = {
            'text': o_text,
            'power': obj.power,
            'toughness': obj.toughness,
            'name': obj.name,
            'flavor': obj.flavor,
            'mana_cost': obj.mana_cost,
            'image_url': obj.image_url,
            'type': obj.type,
        }
        context = {'title': 'Card Image', 'obj': o_card, 'card_set': card_set}
        return render(request, 'app/card_image.html', context)
    except Exception as e:
        return JsonResponse({'Error': str(e)})


def card_search(request):
    try:
        context = {'title': 'Card Search'}
        if request.method == 'POST':
            form = SearchForm(request.POST or None)
            if form.is_valid():
                search = form.cleaned_data['search']
                response = requests.get(SCRYFALL_API + 'cards/search?q=' + search)
                if response.status_code == 200:
                    srch_results = response.json()
                    cards = [
                        dict(
                            code=data['code'],
                            symbol_url=data['icon_svg_uri'],
                            name=data['name'],
                            release_date=data['released_at']
                        ) for data in srch_results['data']
                    ]
                    context['cards'] = cards
            else:
                messages.warning(request, 'Please enter a search term')
        return render(request, 'app/cards.html', context)
    except Exception as e:
        return JsonResponse({'Error': str(e)})
