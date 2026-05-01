# dictionary/urls.py
from django.urls import path
from . import views

app_name = 'dictionary'

urlpatterns = [
    path('', views.dictionary_home, name='home'),
    path('word/<slug:slug>/', views.word_detail, name='word_detail'),
    path('history/', views.word_history, name='history'),
    path('api/lookup/', views.api_lookup_word, name='api_lookup'),
    path('api/suggest/', views.api_suggest_words, name='api_suggest'),
]