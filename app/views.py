import json
import re

import requests
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from mtgsdk import Card
from mtgsdk import Set

from app.forms import SearchForm

SCRYFALL_API = 'https://api.scryfall.com/'
SCRYFALL_SETS = SCRYFALL_API + 'sets/'
SCRYFALL_SYMBOLS = SCRYFALL_API + 'symbology/'
SCRYFALL_URI = 'https://svgs.scryfall.io/card-symbols/'


def toggle_view_mode(request, mode: str = None):
    if mode is not None:
        if mode == 'dark':
            response = HttpResponse('<i id="toggle-mode" class="fa fa-sun-o text-light"></i>')
            response.set_cookie('toggle_mode', 'dark')
        else:
            response = HttpResponse('<i id="toggle-mode" class="fa fa-moon-o text-dark"></i>')
            response.set_cookie('toggle_mode', None)
    else:
        response = HttpResponse('<i id="toggle-mode" class="fa fa-moon-o text-dark"></i>')
        response.set_cookie('toggle_mode', None)
    return response


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
        return render(request, 'app/card_sets.html', {'sets': cards})
    except Exception as e:
        return JsonResponse({'Error': str(e)})


# @cache_page(60 * 15)
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
                'flavor': r.flavor,
                'toughness': r.toughness,
                # 'card_no': r.card_no
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


# @cache_page(60 * 15)
def card_image(request, card_id: str):
    try:
        response = requests.get(SCRYFALL_API + '/cards/' + card_id)
        if response.status_code == 200:
            # print(response.json())
            obj = response.json()
        else:
            obj = {
                'type': '',
                'set': '',
                'text': '',
                'power': None,
                'toughness': None,
                'flavor': '',
                'name': '',
                'mana_cost': '',
                'image_uris': {'normal': ''},
                'oracle_text': ''
            }
        # obj = Card.find(card_id)
        print(obj)
        r_set = requests.get('https://api.scryfall.com/sets/'+obj['set'])
        if r_set.status_code == 200:
            card_set = r_set.json()
        else:
            card_set = None
        o_text = convert_symbols(obj['oracle_text'])
        o_card = {
            'text': o_text,
            'power': obj['power'] if 'power' in obj else None,
            'toughness': obj['toughness'] if 'toughness' in obj else None,
            'name': obj['name'],
            'type': obj['type_line'] if 'type_line' in obj else None,
            'flavor': obj['flavor_text'] if 'flavor_text' in obj else None,
            'mana_cost': obj['mana_cost'],
            'image_url': obj['image_uris']['normal'],
            'set': obj['set'],
            'oracle_text': obj['oracle_text']


        }
        context = {'title': 'Card Image', 'obj': o_card, 'card_set': card_set}
        return render(request, 'app/card_image.html', context)
    except Exception as e:
        return JsonResponse({'Error': str(e)})


def card_search(request):
    try:
        context = {'title': 'Card Search', 'srch_term': ''}
        if request.method == 'POST':
            form = SearchForm(request.POST or None)
            if form.is_valid():
                search = form.cleaned_data['search']
                context['srch_term'] = search
                print(search)
                response = requests.get('https://api.scryfall.com/cards/search?q=%s' % search)
                if response.status_code == 200:
                    srch_results = response.json()['data']
                    if len(srch_results) > 0:
                        cards = [
                            {
                                'id': result['id'],
                                'name': result['name'],
                                'image_url': result['image_uris']['normal'] if 'image_uris' in result else '',
                                'oracle_id': result['oracle_id'],
                                'text': convert_symbols(result['oracle_text']) if 'oracle_text' in result else convert_symbols(result['card_faces'][0]['oracle_text']),
                                'type': result['type_line'],
                                'mana_cost': result['mana_cost'] if 'mana_cost' in result else result['card_faces'][0]['mana_cost'],
                                'flavor': result['flavor_text']
                            }
                            for result in srch_results
                        ]
                        context['cards'] = cards
                else:
                    return JsonResponse({'Response': response.status_code})
        return render(request, 'app/cards.html', context)
    # return HttpResponse('Hello')
    except TypeError as e:
        return JsonResponse({'TypeError': str(e)})
    except Exception as e:
        return JsonResponse({'Error': str(e)})
