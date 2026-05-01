# ai_assistant/urls.py
from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.ai_assistant_home, name='home'),
    path('api/chat/', views.ai_chat_api, name='chat_api'),
    path('api/suggestions/', views.get_suggestions, name='suggestions'),
    path('clear-usage/', views.clear_usage, name='clear_usage'),
]