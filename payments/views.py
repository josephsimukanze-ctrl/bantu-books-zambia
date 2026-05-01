from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def checkout(request):
    """Payment checkout page"""
    messages.info(request, 'Payment system is coming soon. Please check back later.')
    return redirect('accounts:upgrade')

@login_required
def purchase_book(request, slug):
    """Purchase a book"""
    messages.info(request, 'Payment system is coming soon. Please check back later.')
    return redirect('books:book_detail', slug=slug)