from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('purchase/<slug:slug>/', views.purchase_book, name='purchase_book'),
]