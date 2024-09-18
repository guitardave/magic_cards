import json

import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from mtgsdk import Card
from mtgsdk import Set


def get_card_symbols():
    data = {}
    response = requests.get('https://api.scryfall.com/symbology')
    if response.status_code == 200:
        data = response.json()
    # print(data)
    return data


def get_mana_color(color_sym: str) -> str:
    data = get_card_symbols()
    color_img = ''
    for d in data['data']:
        if d['symbol'] == color_sym:
            color_img = d['svg_uri']
    return color_img


# @cache_page
def home(request):
    try:
        card_sets = Set.all()
        return render(request, 'home.html', {'sets': card_sets})
    except Exception as e:
        return JsonResponse({'Error': e})


def card_list(request, set_id: str):
    card_set = Set.find(set_id)
    rs = Card.where(set=set_id).all()
    cards = []
    for r in rs:
        new_mana_cost = tuple(str(r.mana_cost).replace('{', '').replace('}', ''))
        cards.append(
            {
                'name': r.name,
                'og_mana_cost': r.mana_cost,
                'mana_cost': new_mana_cost,
                'color_identity': r.color_identity,
                'colors': r.colors,
                'id': r.id,
                'image_url': r.image_url
            }
        )
        print(new_mana_cost)
    context = {'cards': cards, 'title': 'Card List', 'card_set': card_set}
    return render(request, 'cards.html', context)


def card_image(request, card_id: str):
    obj = Card.find(card_id)
    card_set = Set.find(obj.set)
    context = {'title': 'Card Image', 'obj': obj, 'card_set': card_set}
    return render(request, 'card_image.html', context)
