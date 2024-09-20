from django.urls import path

from app import views

app_name = 'app'

urlpatterns = [
    path('', views.home, name='home'),
    path('cards/<str:set_id>/', views.card_list, name='card_list'),
    path('cards/<str:card_id>/images/', views.card_image, name='card_image'),
    path('search/', views.card_search, name='card_search'),
]
