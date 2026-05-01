from django.shortcuts import render
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from books.models import Book, Category

from django.shortcuts import render
from django.db.models import Count, Q
from books.models import Book, Category, GradeLevel, Language
from accounts.models import User

def home(request):
    """Home page view with real data from database"""
    
    # Real statistics from database
    total_books = Book.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_active=True).count()
    total_authors = Book.objects.filter(is_active=True).values('author').distinct().count()
    total_languages = Language.objects.filter(is_active=True).count()
    
    # Get books for different sections
    recent_books = Book.objects.filter(is_active=True).order_by('-created_at')[:8]
    free_books = Book.objects.filter(is_free=True, is_active=True).order_by('-created_at')[:8]
    popular_books = Book.objects.filter(is_active=True).order_by('-downloads_count')[:8]
    featured_books = Book.objects.filter(is_featured=True, is_active=True)[:6]
    
    # Get categories - DON'T assign to book_count (it's a property)
    categories = Category.objects.filter(is_active=True)
    # The book_count property will be calculated automatically when accessed in template
    
    # Get grade levels with book counts for sidebar
    grade_levels = GradeLevel.objects.filter(is_active=True)
    
    # Get languages with book counts for sidebar
    languages = Language.objects.filter(is_active=True)
    
    context = {
        # Stats
        'total_books': total_books,
        'total_users': total_users,
        'total_authors': total_authors,
        'total_languages': total_languages,
        
        # Books sections
        'recent_books': recent_books,
        'free_books': free_books,
        'popular_books': popular_books,
        'featured_books': featured_books,
        
        # Filter data for sidebar
        'categories': categories,
        'grade_levels': grade_levels,
        'languages': languages,
    }
    return render(request, 'core/home.html', context)
def about(request):
    """About page"""
    return render(request, 'core/about.html')

def contact(request):
    """Contact page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return render(request, 'core/contact.html')
    
    return render(request, 'core/contact.html')

def faq(request):
    """FAQ page"""
    return render(request, 'core/faq.html')

def terms(request):
    """Terms and conditions"""
    return render(request, 'core/terms.html')

def privacy(request):
    """Privacy policy"""
    return render(request, 'core/privacy.html')

# core/views.py
from django.shortcuts import render

def handler404(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', status=500)