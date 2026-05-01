from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.db import models
from .models import Book, Category, GradeLevel, Language
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from .models import Book, Category, GradeLevel, Language
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from .models import Book, Category, GradeLevel, Language
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg  # Add Avg here
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Book, Category, GradeLevel, Language, BookReview  # Add BookReview here
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Book, Category, GradeLevel, Language, BookReview, BookRequest, Contributor, ContributorApplication, ContributorAgreement, ContributorEarning, ContributorWithdrawal
from .models import Book, Category, GradeLevel, Language
from django.db.models import Avg 
from django.utils import timezone
from django.utils import timezone
from django.db.models import Count, Q
from django.shortcuts import render
from .models import Book, Category, GradeLevel, Language
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from books.models import Book, Category, GradeLevel, Language

def category_books(request, slug):
    """Display books in a specific category with all subcategories"""
    
    # Get the current category
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get all subcategories for display
    subcategories = category.subcategories.filter(is_active=True).order_by('order')
    
    # Build category hierarchy for breadcrumbs
    category_hierarchy = []
    current = category
    while current:
        category_hierarchy.insert(0, current)
        current = current.parent
    
    # Get all category IDs including the current category and all its descendants
    category_ids = [category.id]
    for subcat in subcategories:
        category_ids.append(subcat.id)
        # Add level 2 categories (subjects) under each subcategory
        for subject in subcat.subcategories.filter(is_active=True):
            category_ids.append(subcat.id)  # This should be subject.id, fix below
            category_ids.append(subject.id)
    
    # Better way: Get all descendant category IDs
    def get_descendant_ids(cat):
        ids = [cat.id]
        for child in cat.subcategories.filter(is_active=True):
            ids.extend(get_descendant_ids(child))
        return ids
    
    # Use recursive function to get all categories in this branch
    all_category_ids = get_descendant_ids(category)
    
    # Get books in any of these categories (including subcategories)
    books_query = Book.objects.filter(
        category_id__in=all_category_ids,
        is_active=True
    ).select_related('category', 'grade_level', 'language')
    
    # Apply filters
    sort_by = request.GET.get('sort', 'latest')
    grade_level = request.GET.get('grade_level')
    language = request.GET.get('language')
    is_free = request.GET.get('is_free')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Grade level filter
    if grade_level:
        books_query = books_query.filter(grade_level_id=grade_level)
    
    # Language filter
    if language:
        books_query = books_query.filter(language_id=language)
    
    # Price filters
    if is_free == 'true':
        books_query = books_query.filter(is_free=True)
    elif is_free == 'false':
        books_query = books_query.filter(is_free=False)
    
    if min_price:
        try:
            books_query = books_query.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            books_query = books_query.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Sorting
    if sort_by == 'latest':
        books_query = books_query.order_by('-created_at')
    elif sort_by == 'popular':
        books_query = books_query.order_by('-downloads_count')
    elif sort_by == 'title_asc':
        books_query = books_query.order_by('title')
    elif sort_by == 'title_desc':
        books_query = books_query.order_by('-title')
    elif sort_by == 'price_asc':
        books_query = books_query.order_by('price')
    elif sort_by == 'price_desc':
        books_query = books_query.order_by('-price')
    else:
        books_query = books_query.order_by('-created_at')
    
    # Remove the line that tries to increment category.views_count
    # Category doesn't have a views_count field
    # category.views_count += 1  # DELETE THIS LINE
    # category.save()  # DELETE THIS LINE
    
    # Instead, if you want to track category views, add the field to Category model
    # Then uncomment the lines above
    
    # Pagination
    paginator = Paginator(books_query, 12)
    page = request.GET.get('page', 1)
    
    try:
        books = paginator.page(page)
    except PageNotAnInteger:
        books = paginator.page(1)
    except EmptyPage:
        books = paginator.page(paginator.num_pages)
    
    # Get filter options
    grade_levels = GradeLevel.objects.filter(is_active=True).order_by('order')
    languages = Language.objects.filter(is_active=True).order_by('order')
    
    # Prepare subcategories with book counts
    subcategories_with_counts = []
    for subcat in subcategories:
        # Get all descendant category IDs for this subcategory
        subcat_descendant_ids = get_descendant_ids(subcat)
        book_count = Book.objects.filter(
            category_id__in=subcat_descendant_ids,
            is_active=True
        ).count()
        
        subcategories_with_counts.append({
            'id': subcat.id,
            'name': subcat.name,
            'slug': subcat.slug,
            'level': subcat.level,
            'description': subcat.description,
            'icon': subcat.icon,
            'book_count': book_count,
            'has_children': subcat.subcategories.filter(is_active=True).exists()
        })
    
    # Active filters for display
    active_filters = []
    
    if grade_level:
        grade = grade_levels.filter(id=grade_level).first()
        if grade:
            active_filters.append({
                'label': f'Grade: {grade.name}',
                'clear_url': remove_query_param(request, 'grade_level')
            })
    
    if language:
        lang = languages.filter(id=language).first()
        if lang:
            active_filters.append({
                'label': f'Language: {lang.name}',
                'clear_url': remove_query_param(request, 'language')
            })
    
    if is_free == 'true':
        active_filters.append({
            'label': 'Free Books Only',
            'clear_url': remove_query_param(request, 'is_free')
        })
    
    # Get popular categories for empty state
    popular_categories = Category.objects.filter(
        level=0,
        is_active=True
    ).annotate(
        book_count=Count('books')
    ).filter(book_count__gt=0).order_by('-book_count')[:5]
    
    context = {
        'category': category,
        'subcategories': subcategories_with_counts,
        'category_hierarchy': category_hierarchy,
        'books': books,
        'current_category': category,
        'current_category_slug': category.slug,
        'current_sort': sort_by,
        'grade_levels': grade_levels,
        'languages': languages,
        'active_filters': active_filters,
        'active_filters_count': len(active_filters),
        'popular_categories': popular_categories,
        'view_mode': request.session.get('book_view_mode', 'grid'),
        'is_category_page': True,
    }
    
    return render(request, 'books/book_list.html', context)


from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.http import JsonResponse
from books.models import Book, Category, GradeLevel, Language
import json
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.http import JsonResponse
from books.models import Book, Category, GradeLevel, Language
import json

def book_list(request):
    """Display books and categories with hierarchical navigation"""
    
    # Get filter parameters
    category_slug = request.GET.get('category')
    sort_by = request.GET.get('sort', 'latest')
    search = request.GET.get('search', '')
    
    # Get the current category
    current_category = None
    category_hierarchy = []
    subcategories = []
    all_top_categories = []
    
    if category_slug:
        # User clicked on a specific category
        current_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        
        # Get category hierarchy for breadcrumb
        temp = current_category
        hierarchy = []
        while temp:
            hierarchy.insert(0, temp)
            temp = temp.parent
        category_hierarchy = hierarchy
        
        # Get direct subcategories of the current category
        subcategories = Category.objects.filter(
            parent=current_category, 
            is_active=True
        ).order_by('order').annotate(
            book_count=Count('books', filter=Q(books__is_active=True))
        )
        
        # Get books in this category (including all descendants)
        def get_descendant_ids(cat):
            ids = [cat.id]
            for child in cat.subcategories.filter(is_active=True):
                ids.extend(get_descendant_ids(child))
            return ids
        
        category_ids = get_descendant_ids(current_category)
        books_query = Book.objects.filter(
            category_id__in=category_ids,
            is_active=True
        ).select_related('category', 'grade_level', 'language')
    else:
        # No category selected - show ALL top-level categories
        current_category = None
        category_hierarchy = []
        
        # Get all top-level categories (no parent) for the main view
        all_top_categories = Category.objects.filter(
            parent__isnull=True,  # Top-level categories only
            is_active=True
        ).order_by('order').annotate(
            book_count=Count('books', filter=Q(books__is_active=True))
        )
        
        # For the main view, also show all categories that should be visible
        # This includes top-level categories and any other categories without a parent filter
        subcategories = all_top_categories
        
        # Get all books (or filter by search)
        books_query = Book.objects.filter(is_active=True).select_related('category', 'grade_level', 'language')
    
    # Apply search filter
    if search:
        books_query = books_query.filter(
            Q(title__icontains=search) |
            Q(author__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Apply sorting
    if sort_by == 'latest':
        books_query = books_query.order_by('-created_at')
    elif sort_by == 'popular':
        books_query = books_query.order_by('-downloads_count')
    elif sort_by == 'title_asc':
        books_query = books_query.order_by('title')
    elif sort_by == 'title_desc':
        books_query = books_query.order_by('-title')
    elif sort_by == 'price_asc':
        books_query = books_query.order_by('price')
    elif sort_by == 'price_desc':
        books_query = books_query.order_by('-price')
    else:
        books_query = books_query.order_by('-created_at')
    
    # Pagination for books (only if we're in a category or search)
    books = None
    show_books = current_category is not None or search
    
    if show_books and books_query.exists():
        paginator = Paginator(books_query, 12)
        page = request.GET.get('page', 1)
        try:
            books = paginator.page(page)
        except PageNotAnInteger:
            books = paginator.page(1)
        except EmptyPage:
            books = paginator.page(paginator.num_pages)
    
    # For debugging - print to console
    print(f"Current category: {current_category}")
    print(f"Subcategories count: {subcategories.count() if hasattr(subcategories, 'count') else len(subcategories)}")
    print(f"All top categories: {[c.name for c in all_top_categories]}")
    
    # Prepare context
    context = {
        'current_category': current_category,
        'category_hierarchy': category_hierarchy,
        'subcategories': subcategories,
        'all_categories': all_top_categories,
        'books': books,
        'current_sort': sort_by,
        'current_category_slug': category_slug,
        'total_books': books_query.count() if hasattr(books_query, 'count') else 0,
        'show_books': show_books,
    }
    
    return render(request, 'books/book_list.html', context)

def quick_view_api(request, slug):
    """API endpoint for quick book view modal"""
    from django.urls import reverse
    
    try:
        book = get_object_or_404(Book, slug=slug, is_active=True)
        data = {
            'title': book.title,
            'author': book.author,
            'description': book.description[:300] if book.description else '',
            'cover_image': book.cover_image.url if book.cover_image else None,
            'price': str(book.price),
            'is_free': book.is_free,
            'downloads_count': book.downloads_count,
            'views_count': book.views_count,
            'category': book.category.name.split(' - ')[-1] if book.category and ' - ' in book.category.name else (book.category.name if book.category else None),
            'detail_url': reverse('books:book_detail', args=[book.slug])
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

def remove_query_param(request, param):
    """Helper function to remove a query parameter from the current URL"""
    get_copy = request.GET.copy()
    if param in get_copy:
        del get_copy[param]
    return f"{request.path}?{get_copy.urlencode()}" if get_copy else request.path
from django.http import JsonResponse
from books.models import Category

@staff_member_required
def get_category_api(request, category_id):
    """Get category details for editing"""
    category = get_object_or_404(Category, id=category_id)
    data = {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'parent_id': category.parent_id,
        'icon': category.icon,
        'description': category.description,
        'order': category.order,
        'is_active': category.is_active,
        'cover_image': category.cover_image.url if category.cover_image else None,
        'level': category.level,
        'book_count': category.books.count(),
    }
    return JsonResponse(data)
from .models import Book, Category, BookReview

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.core.paginator import Paginator
from books.models import Book, BookReview, Category
from downloads.models import Purchase, SavedBook, BookDownload, BookView
import logging

logger = logging.getLogger(__name__)


from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.db.models import Avg, Count
from books.models import Book, BookReview

def book_detail(request, slug):
    """Book detail view with reviews"""
    book = get_object_or_404(Book, slug=slug, is_active=True)
    
    # Increment view count
    from django.db.models import F
    Book.objects.filter(id=book.id).update(views_count=F('views_count') + 1)
    book.refresh_from_db()
    
    # Get ALL reviews (not filtering by is_approved since default is True)
    reviews = BookReview.objects.filter(
        book=book
    ).select_related('user').order_by('-created_at')
    
    # Get average rating
    from django.db.models import Avg
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Get total reviews count
    total_reviews = reviews.count()
    
    print(f"Book: {book.title} - Found {total_reviews} reviews")  # Debug
    
    # Get related books
    related_books = []
    if book.category:
        related_books = Book.objects.filter(
            category=book.category,
            is_active=True
        ).exclude(id=book.id)[:4]
    
    # Check if user has purchased
    has_purchased = False
    if request.user.is_authenticated and not book.is_free:
        from downloads.models import Purchase
        has_purchased = Purchase.objects.filter(
            user=request.user,
            book=book,
            status='completed'
        ).exists()
    
    context = {
        'book': book,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
        'related_books': related_books,
        'has_purchased': has_purchased,
    }
    
    return render(request, 'books/book_detail.html', context)
    
    # Get file size in MB for display
    file_size_mb = None
    if book.pdf_file:
        try:
            file_size_mb = round(book.pdf_file.size / (1024 * 1024), 2)
        except:
            pass
    
    context = {
        'book': book,
        'reviews': reviews_page,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': reviews.count(),
        'rating_counts': rating_counts,
        'related_books': related_books,
        'has_purchased': has_purchased,
        'is_saved': is_saved,
        'file_size_mb': file_size_mb,
    }
    
    return render(request, 'books/book_detail.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
from books.models import Book, BookReview
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from books.models import Book, BookReview
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from books.models import Book, BookReview
import json

@login_required
def add_review(request, slug):
    """Add or update a book review - Auto-approve immediately"""
    book = get_object_or_404(Book, slug=slug, is_active=True)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        # Debug print
        print(f"Received review - Rating: {rating}, Comment: {comment}, User: {request.user.username}")
        
        if not rating:
            messages.error(request, 'Please select a rating.')
            return redirect('books:book_detail', slug=book.slug)
        
        if not comment:
            messages.error(request, 'Please enter a comment.')
            return redirect('books:book_detail', slug=book.slug)
        
        try:
            rating_value = int(rating)
            if rating_value < 1 or rating_value > 5:
                messages.error(request, 'Rating must be between 1 and 5.')
                return redirect('books:book_detail', slug=book.slug)
            
            # Check if user already reviewed this book
            existing_review = BookReview.objects.filter(
                book=book, 
                user=request.user
            ).first()
            
            if existing_review:
                # Update existing review
                existing_review.rating = rating_value
                existing_review.comment = comment
                existing_review.is_approved = True
                existing_review.save()
                messages.success(request, 'Your review has been updated!')
                print(f"Updated review for {request.user.username}")
            else:
                # Create new review
                new_review = BookReview.objects.create(
                    book=book,
                    user=request.user,
                    rating=rating_value,
                    comment=comment,
                    is_approved=True  # This ensures immediate display
                )
                messages.success(request, 'Thank you for your review!')
                print(f"Created new review for {request.user.username} with rating {rating_value}")
            
            return redirect('books:book_detail', slug=book.slug)
            
        except ValueError:
            messages.error(request, 'Invalid rating value.')
            return redirect('books:book_detail', slug=book.slug)
        except Exception as e:
            print(f"Error saving review: {e}")
            messages.error(request, f'Error saving review: {str(e)}')
            return redirect('books:book_detail', slug=book.slug)
    
    return redirect('books:book_detail', slug=book.slug)
@login_required
def save_book(request, slug):
    """Save or unsave a book to user's library"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
    
    book = get_object_or_404(Book, slug=slug, is_active=True)
    
    saved_book, created = SavedBook.objects.get_or_create(
        user=request.user,
        book=book
    )
    
    if created:
        return JsonResponse({
            'success': True,
            'message': 'Book saved to your library',
            'action': 'saved'
        })
    else:
        saved_book.delete()
        return JsonResponse({
            'success': True,
            'message': 'Book removed from your library',
            'action': 'unsaved'
        })


@login_required
def is_book_saved(request, slug):
    """Check if a book is saved by the user (AJAX)"""
    book = get_object_or_404(Book, slug=slug, is_active=True)
    
    is_saved = SavedBook.objects.filter(
        user=request.user,
        book=book
    ).exists()
    
    return JsonResponse({'is_saved': is_saved})


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def my_library(request):
    """Display user's saved books"""
    saved_books = SavedBook.objects.filter(
        user=request.user
    ).select_related('book').order_by('-saved_at')
    
    paginator = Paginator(saved_books, 12)
    page = request.GET.get('page', 1)
    saved_books_page = paginator.get_page(page)
    
    context = {
        'saved_books': saved_books_page,
        'total_saved': saved_books.count(),
    }
    
    return render(request, 'books/my_library.html', context)


@login_required
def my_purchases(request):
    """Display user's purchased books"""
    purchases = Purchase.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('book').order_by('-purchased_at')
    
    paginator = Paginator(purchases, 12)
    page = request.GET.get('page', 1)
    purchases_page = paginator.get_page(page)
    
    total_spent = purchases.aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    context = {
        'purchases': purchases_page,
        'total_purchases': purchases.count(),
        'total_spent': total_spent,
    }
    
    return render(request, 'books/my_purchases.html', context)


def track_view(request, slug):
    """AJAX endpoint to track book views"""
    if request.method != 'GET':
        return JsonResponse({'success': False}, status=400)
    
    book = get_object_or_404(Book, slug=slug, is_active=True)
    
    # Increment view count
    from django.db.models import F
    Book.objects.filter(id=book.id).update(views_count=F('views_count') + 1)
    
    # Track view for authenticated users
    if request.user.is_authenticated:
        try:
            BookView.objects.create(
                book=book,
                user=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                referrer=request.META.get('HTTP_REFERER', '')[:500],
                session_id=request.session.session_key
            )
        except Exception as e:
            logger.error(f"Error tracking view: {e}")
    
    return JsonResponse({'success': True})

def search_books(request):
    """Advanced search with filters, sorting, and suggestions"""
    
    # Get search parameters
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    category_filter = request.GET.get('category', '')
    grade_filter = request.GET.get('grade', '')
    language_filter = request.GET.get('language', '')
    price_filter = request.GET.get('price', '')
    sort_by = request.GET.get('sort', 'relevance')
    format_type = request.GET.get('format', 'html')  # For JSON responses
    
    # Start with active books
    books = Book.objects.filter(is_active=True)
    
    # Apply search query
    if query:
        if search_type == 'title':
            books = books.filter(title__icontains=query)
        elif search_type == 'author':
            books = books.filter(author__icontains=query)
        elif search_type == 'description':
            books = books.filter(description__icontains=query)
        else:  # all fields
            books = books.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(description__icontains=query)
            )
    
    # Apply filters
    if category_filter:
        books = books.filter(category__slug=category_filter)
    
    if grade_filter:
        books = books.filter(grade_level__slug=grade_filter)
    
    if language_filter:
        books = books.filter(language__code=language_filter)
    
    if price_filter == 'free':
        books = books.filter(is_free=True)
    elif price_filter == 'paid':
        books = books.filter(is_free=False)
    
    # Apply sorting
    if sort_by == 'newest':
        books = books.order_by('-created_at')
    elif sort_by == 'oldest':
        books = books.order_by('created_at')
    elif sort_by == 'popular':
        books = books.order_by('-downloads_count')
    elif sort_by == 'title_asc':
        books = books.order_by('title')
    elif sort_by == 'title_desc':
        books = books.order_by('-title')
    elif sort_by == 'price_asc':
        books = books.order_by('price')
    elif sort_by == 'price_desc':
        books = books.order_by('-price')
    else:  # relevance - default
        books = books.order_by('-created_at')
    
    # Get total results count
    total_results = books.count()
    
    # Check if this is an AJAX/JSON request for live search
    if format_type == 'json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON response for live search
        books_list = []
        for book in books[:10]:  # Limit to 10 for live search
            books_list.append({
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'slug': book.slug,
                'cover_url': book.cover_image.url if book.cover_image else None,
                'is_free': book.is_free,
                'price': str(book.price),
                'formatted_price': book.formatted_price,
            })
        return JsonResponse({'books': books_list, 'total': total_results})
    
    # Pagination for HTML view
    paginator = Paginator(books, 12)
    page = request.GET.get('page', 1)
    try:
        books_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        books_page = paginator.page(1)
    
    # Get suggestions for empty results
    suggestions = []
    if not books and query:
        # Suggest similar categories
        category_suggestions = Category.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )[:3]
        for cat in category_suggestions:
            suggestions.append({
                'type': 'category',
                'name': cat.name,
                'url': f"/books/?category={cat.slug}",
                'count': cat.book_count
            })
        
        # Suggest similar books from same author
        author_suggestions = Book.objects.filter(
            author__icontains=query,
            is_active=True
        ).values('author').annotate(count=Count('id')).order_by('-count')[:2]
        
        for author in author_suggestions:
            suggestions.append({
                'type': 'author',
                'name': author['author'],
                'url': f"/books/search/?q={author['author']}",
                'count': author['count']
            })
    
    # Get related categories for filtering
    categories = Category.objects.filter(is_active=True)[:8]
    grade_levels = GradeLevel.objects.filter(is_active=True)[:6]
    languages = Language.objects.filter(is_active=True)[:6]
    
    context = {
        'query': query,
        'search_type': search_type,
        'books': books_page,
        'total_results': total_results,
        'suggestions': suggestions,
        'categories': categories,
        'grade_levels': grade_levels,
        'languages': languages,
        'current_category': category_filter,
        'current_grade': grade_filter,
        'current_language': language_filter,
        'current_price': price_filter,
        'current_sort': sort_by,
        'has_previous': books_page.has_previous(),
        'has_next': books_page.has_next(),  # Fixed: use has_next() not hasNext()
        'page_range': paginator.page_range,
        'current_page': books_page.number,
        'total_pages': paginator.num_pages,
    }
    
    return render(request, 'books/search_results.html', context)
def ajax_load_books(request):
    """AJAX endpoint for loading more books (infinite scroll)"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return redirect('books:book_list')
    
    page = request.GET.get('page', 1)
    books = Book.objects.filter(is_active=True).order_by('-created_at')
    
    paginator = Paginator(books, 12)
    try:
        books_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        books_page = paginator.page(1)
    
    context = {
        'books': books_page,
    }
    return render(request, 'books/partials/book_list_partial.html', context)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from books.models import Book

def track_view(request, slug):
    """Track book view - accepts both GET and POST"""
    try:
        book = get_object_or_404(Book, slug=slug, is_active=True)
        book.views_count += 1
        book.save(update_fields=['views_count'])
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

from django.contrib.auth.decorators import login_required
from .models import BookRequest
from django.core.mail import send_mail
from django.conf import settings

@login_required
def request_book(request):
    """View for users to request a book"""
    
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        reason = request.POST.get('reason')
        priority = request.POST.get('priority', 'medium')
        email = request.POST.get('email', request.user.email)
        
        if not title:
            messages.error(request, 'Please provide the book title.')
            return redirect('books:request_book')
        
        # Create the request
        book_request = BookRequest.objects.create(
            user=request.user,
            email=email,
            title=title,
            author=author,
            isbn=isbn,
            category_id=category_id if category_id else None,
            description=description,
            reason=reason,
            priority=priority
        )
        
        # Send confirmation email
        try:
            send_mail(
                subject=f'Book Request Received: {title}',
                message=f"""
                Hello {request.user.get_full_name() or request.user.username},
                
                Thank you for your book request! We have received your request for:
                
                Title: {title}
                Author: {author or 'Not specified'}
                Priority: {priority}
                
                Request ID: #{book_request.id}
                
                Our team will review your request and get back to you soon.
                
                You can track your request status here:
                {request.build_absolute_uri(reverse('books:my_requests'))}
                
                Thank you for using Bantu Books Zambia!
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email error: {e}")
        
        messages.success(request, f'Your request for "{title}" has been submitted successfully! We will notify you once it\'s available.')
        return redirect('books:my_requests')
    
    # GET request - show form
    categories = Category.objects.filter(is_active=True)
    context = {
        'categories': categories,
    }
    return render(request, 'books/request_book.html', context)


@login_required
def my_requests(request):
    """View user's book requests"""
    requests = BookRequest.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'requests': requests,
        'total_requests': requests.count(),
        'pending_requests': requests.filter(status='pending').count(),
        'approved_requests': requests.filter(status='approved').count(),
        'completed_requests': requests.filter(status='completed').count(),
    }
    return render(request, 'books/my_requests.html', context)

@login_required
def received_books(request):
    """View books that were sent to the user via requests"""
    received_requests = BookRequest.objects.filter(
        user=request.user,
        status='completed',
        assigned_book__isnull=False
    ).select_related('assigned_book')
    
    context = {
        'received_books': received_requests,
        'total_received': received_requests.count(),
    }
    return render(request, 'books/received_books.html', context)

from django.contrib.admin.views.decorators import staff_member_required
from .models import BookRequest, Book

@staff_member_required
def staff_manage_requests(request):
    """Staff view to manage book requests"""
    all_requests = BookRequest.objects.all().order_by('-created_at')
    available_books = Book.objects.filter(is_active=True)
    
    context = {
        'all_requests': all_requests,
        'total_requests': all_requests.count(),
        'pending_count': all_requests.filter(status='pending').count(),
        'approved_count': all_requests.filter(status='approved').count(),
        'processing_count': all_requests.filter(status='processing').count(),
        'completed_count': all_requests.filter(status='completed').count(),
        'rejected_count': all_requests.filter(status='rejected').count(),
        'available_books': available_books,
    }
    return render(request, 'books/staff_manage_requests.html', context)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from books.models import Book, BookReview

@login_required
def add_review(request, slug):
    """Add or update a book review via AJAX or regular POST"""
    book = get_object_or_404(Book, slug=slug, is_active=True)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating and comment:
            try:
                rating_value = int(rating)
                if 1 <= rating_value <= 5:
                    # Check if user already reviewed
                    existing_review = BookReview.objects.filter(
                        book=book, 
                        user=request.user
                    ).first()
                    
                    if existing_review:
                        existing_review.rating = rating_value
                        existing_review.comment = comment
                        existing_review.is_approved = False
                        existing_review.save()
                        messages.success(request, 'Your review has been updated and is pending approval!')
                    else:
                        BookReview.objects.create(
                            book=book,
                            user=request.user,
                            rating=rating_value,
                            comment=comment,
                            is_approved=False
                        )
                        messages.success(request, 'Thank you for your review! It will appear after approval.')
                    
                    # If AJAX request, return JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': 'Review submitted successfully'})
                    
                    return redirect('books:book_detail', slug=book.slug)
                else:
                    error_msg = 'Rating must be between 1 and 5.'
            except ValueError:
                error_msg = 'Invalid rating value.'
        else:
            error_msg = 'Please provide both a rating and a comment.'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        else:
            messages.error(request, error_msg)
            return redirect('books:book_detail', slug=book.slug)
    
    return redirect('books:book_detail', slug=book.slug)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

@staff_member_required
@require_POST
@csrf_exempt
def api_approve_request(request, request_id):
    """API endpoint to approve a request"""
    try:
        book_request = BookRequest.objects.get(id=request_id)
        book_request.status = 'approved'
        book_request.save()
        
        # Send email notification
        try:
            send_mail(
                subject=f'Book Request Approved: {book_request.title}',
                message=f"""
                Hello {book_request.user.get_full_name() or book_request.user.username},
                
                Your request for "{book_request.title}" has been approved!
                
                We are now working on adding this book to our library. You will receive another notification once the book is available.
                
                Thank you for using Bantu Books Zambia!
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[book_request.email],
                fail_silently=True,
            )
        except:
            pass
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@staff_member_required
@require_POST
@csrf_exempt
def api_reject_request(request, request_id):
    """API endpoint to reject a request"""
    try:
        book_request = BookRequest.objects.get(id=request_id)
        book_request.status = 'rejected'
        book_request.save()
        
        # Send email notification
        try:
            send_mail(
                subject=f'Book Request Update: {book_request.title}',
                message=f"""
                Hello {book_request.user.get_full_name() or book_request.user.username},
                
                Thank you for your request for "{book_request.title}".
                
                Unfortunately, we are unable to fulfill this request at this time.
                
                You can try searching for alternative books or make a new request.
                
                Thank you for understanding!
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[book_request.email],
                fail_silently=True,
            )
        except:
            pass
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@staff_member_required
def admin_add_book_to_request(request, request_id):
    """Admin adds a book to fulfill a request"""
    book_request = get_object_or_404(BookRequest, id=request_id)
    
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        if book_id:
            book = get_object_or_404(Book, id=book_id)
            book_request.assigned_book = book
            book_request.book_added_at = timezone.now()
            book_request.status = 'completed'
            book_request.save()
            
            # Send email notification
            try:
                send_mail(
                    subject=f'Book Available: {book.title}',
                    message=f"""
                    Hello {book_request.user.get_full_name() or book_request.user.username},
                    
                    Great news! The book you requested is now available!
                    
                    Book: {book.title}
                    Author: {book.author}
                    
                    You can download it here:
                    {request.build_absolute_uri(reverse('books:book_detail', args=[book.slug]))}
                    
                    Thank you for using Bantu Books Zambia!
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[book_request.email],
                    fail_silently=False,
                )
                book_request.notified_at = timezone.now()
                book_request.notified_by = request.user
                book_request.save()
            except Exception as e:
                messages.warning(request, f'Book assigned but email could not be sent: {e}')
            
            messages.success(request, f'Book "{book.title}" assigned to request and user notified!')
            return redirect('books:staff_manage_requests')
    
    return redirect('books:staff_manage_requests')


@staff_member_required
def view_user_profile(request, user_id):
    """Staff view to see user profile details"""
    from accounts.models import User
    from downloads.models import BookDownload, BookReadOnline, BookView
    from books.models import BookRequest
    
    user = get_object_or_404(User, id=user_id)
    
    # Get user statistics
    total_downloads = BookDownload.objects.filter(user=user).count()
    total_views = BookView.objects.filter(user=user).count()
    total_reads = BookReadOnline.objects.filter(user=user).count()
    total_requests = BookRequest.objects.filter(user=user).count()
    pending_requests = BookRequest.objects.filter(user=user, status='pending').count()
    completed_requests = BookRequest.objects.filter(user=user, status='completed').count()
    
    # Get recent downloads
    recent_downloads = BookDownload.objects.filter(user=user).select_related('book')[:10]
    
    # Get recent requests
    recent_requests = BookRequest.objects.filter(user=user).order_by('-created_at')[:10]
    
    context = {
        'profile_user': user,
        'total_downloads': total_downloads,
        'total_views': total_views,
        'total_reads': total_reads,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'completed_requests': completed_requests,
        'recent_downloads': recent_downloads,
        'recent_requests': recent_requests,
    }
    return render(request, 'books/view_user_profile.html', context)




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import ContributorApplication, ContributorAgreement, Contributor, ContributorWithdrawal
import json
import base64

@login_required
def apply_contributor(request):
    """Apply to become a contributor"""
    # Check if already applied
    existing_app = ContributorApplication.objects.filter(user=request.user).first()
    if existing_app:
        messages.warning(request, f'You already have an application {existing_app.get_status_display()}.')
        return redirect('books:contributor_dashboard')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        teaching_experience = request.POST.get('teaching_experience', '')
        writing_experience = request.POST.get('writing_experience', '')
        subject_specialization = request.POST.get('subject_specialization', '')
        reason = request.POST.get('reason_to_contribute')
        grade12_cert = request.FILES.get('grade12_certificate')
        nrc_doc = request.FILES.get('nrc_document')
        
        if not all([full_name, email, phone_number, address, reason, grade12_cert, nrc_doc]):
            messages.error(request, 'Please fill all required fields.')
            return redirect('books:apply_contributor')
        
        application = ContributorApplication.objects.create(
            user=request.user,
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            address=address,
            teaching_experience=teaching_experience,
            writing_experience=writing_experience,
            subject_specialization=subject_specialization,
            reason_to_contribute=reason,
            grade12_certificate=grade12_cert,
            nrc_document=nrc_doc,
            status='pending'
        )
        
        messages.success(request, 'Your application has been submitted! We will review it shortly.')
        return redirect('books:contributor_dashboard')
    
    return render(request, 'books/apply_contributor.html')

@login_required
def contributor_dashboard(request):
    """Contributor dashboard with earnings and agreement"""
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta
    from decimal import Decimal
    
    try:
        contributor = Contributor.objects.get(user=request.user)
        applications = ContributorApplication.objects.filter(user=request.user)
        has_application = applications.exists()
        application = applications.first() if has_application else None
        
        # Check if agreement is signed
        agreement_signed = contributor.application and contributor.application.agreement_signed if contributor.application else False
        
        # ============ EARNINGS STATISTICS ============
        # Get earnings
        earnings = ContributorEarning.objects.filter(contributor=contributor).order_by('-created_at')[:10]
        total_earnings = ContributorEarning.objects.filter(contributor=contributor).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # This month's earnings
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        monthly_earnings = ContributorEarning.objects.filter(
            contributor=contributor,
            created_at__date__gte=start_of_month
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # Last month's earnings (for trend)
        last_month_start = start_of_month - timedelta(days=30)
        last_month_end = start_of_month - timedelta(days=1)
        last_month_earnings = ContributorEarning.objects.filter(
            contributor=contributor,
            created_at__date__gte=last_month_start,
            created_at__date__lte=last_month_end
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # Calculate earnings trend
        earnings_trend = 0
        if last_month_earnings > 0:
            earnings_trend = round(((monthly_earnings - last_month_earnings) / last_month_earnings) * 100, 1)
        elif monthly_earnings > 0:
            earnings_trend = 100
        
        # ============ BOOK STATISTICS ============
        # Get books uploaded by contributor
        recent_books = Book.objects.filter(contributor=contributor).order_by('-created_at')[:10]
        total_books_uploaded = Book.objects.filter(contributor=contributor).count()
        
        # Approved vs Pending books
        approved_books_count = Book.objects.filter(contributor=contributor, is_active=True).count()
        pending_books_count = Book.objects.filter(contributor=contributor, is_active=False).count()
        
        # Total downloads and views from contributor's books
        book_stats = Book.objects.filter(contributor=contributor).aggregate(
            total_downloads=Sum('downloads_count'),
            total_views=Sum('views_count')
        )
        total_downloads = book_stats['total_downloads'] or 0
        total_views = book_stats['total_views'] or 0
        
        # ============ UPLOAD LIMITS ============
        today = timezone.now().date()
        uploaded_today = Book.objects.filter(
            contributor=contributor,
            created_at__date=today
        ).count()
        daily_limit = 10
        remaining_uploads = max(0, daily_limit - uploaded_today)
        uploads_used = uploaded_today
        
        # ============ WITHDRAWAL HISTORY ============
        withdrawals = ContributorWithdrawal.objects.filter(contributor=contributor).order_by('-created_at')[:10]
        
        # Calculate amount needed for withdrawal
        min_withdrawal = 250
        amount_needed = max(0, min_withdrawal - contributor.available_balance)
        
        # ============ MEMBERSHIP DURATION ============
        member_since = contributor.created_at.date()
        member_since_days = (today - member_since).days
        
        # ============ CONTEXT BUILDING ============
        context = {
            # Contributor info
            'contributor': contributor,
            'has_application': has_application,
            'application': application,
            'agreement_signed': agreement_signed,
            
            # Earnings
            'earnings': earnings,
            'total_earnings': total_earnings,
            'available_balance': contributor.available_balance,
            'monthly_earnings': monthly_earnings,
            'earnings_trend': earnings_trend,
            'amount_needed': amount_needed,
            
            # Books
            'recent_books': recent_books,
            'total_books_uploaded': total_books_uploaded,
            'approved_books_count': approved_books_count,
            'pending_books_count': pending_books_count,
            
            # Stats
            'total_downloads': total_downloads,
            'total_views': total_views,
            
            # Upload limits
            'remaining_uploads': remaining_uploads,
            'uploads_used': uploads_used,
            'daily_limit': daily_limit,
            
            # Withdrawals
            'withdrawals': withdrawals,
            
            # Membership
            'member_since': member_since,
            'member_since_days': member_since_days,
        }
        
    except Contributor.DoesNotExist:
        # Check if user has an application
        applications = ContributorApplication.objects.filter(user=request.user)
        has_application = applications.exists()
        application = applications.first() if has_application else None
        
        context = {
            'contributor': None,
            'has_application': has_application,
            'application': application,
            'agreement_signed': application.agreement_signed if application else False,
            'total_earnings': Decimal('0.00'),
            'available_balance': Decimal('0.00'),
            'total_books_uploaded': 0,
            'approved_books_count': 0,
            'pending_books_count': 0,
            'total_downloads': 0,
            'total_views': 0,
            'remaining_uploads': 10,
            'uploads_used': 0,
            'daily_limit': 10,
            'member_since_days': 0,
        }
    
    return render(request, 'books/contributor_dashboard.html', context)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from books.models import ContributorApplication, ContributorAgreement, Contributor

@login_required
def sign_agreement(request, application_id):
    """Sign the contributor agreement"""
    application = get_object_or_404(ContributorApplication, id=application_id, user=request.user)
    
    if application.status != 'approved':
        messages.error(request, 'Your application must be approved before signing agreement.')
        return redirect('books:contributor_dashboard')
    
    # Get the latest active agreement
    agreement = ContributorAgreement.objects.filter(is_active=True).first()
    
    if not agreement:
        # Create default agreement if none exists
        agreement = ContributorAgreement.objects.create(
            title="Contributor Agreement",
            content="""
            <h3>Terms and Conditions</h3>
            <p><strong>1. Content Ownership:</strong> You retain ownership of your content but grant Bantu Books Zambia a non-exclusive license to distribute and sell your books.</p>
            <p><strong>2. Earnings:</strong> You will earn K5.00 for each book uploaded and approved. Payments are made monthly on the 15th for the previous month's earnings.</p>
            <p><strong>3. Content Guidelines:</strong> All content must be original, educational, and appropriate for Zambian students. Plagiarism is strictly prohibited.</p>
            <p><strong>4. Quality Standards:</strong> Books must meet our quality standards including proper formatting, accurate information, and clear presentation.</p>
            <p><strong>5. Withdrawal:</strong> Minimum withdrawal amount is K250. Withdrawals can be requested once per month.</p>
            <p><strong>6. Termination:</strong> Either party may terminate this agreement with 30 days written notice. Violation of terms may result in immediate termination.</p>
            <p><strong>7. Liability:</strong> Bantu Books Zambia is not liable for any claims arising from your content. You agree to indemnify the platform.</p>
            """,
            version="1.0",
            is_active=True
        )
    
    # Check if already signed
    if application.agreement_signed:
        messages.info(request, 'You have already signed the agreement.')
        return redirect('books:contributor_dashboard')
    
    if request.method == 'POST':
        signature_data = request.POST.get('signature_data')
        
        if not signature_data:
            messages.error(request, 'Please provide your signature.')
            return redirect('books:sign_agreement', application_id=application_id)
        
        # Save signature
        application.agreement_signature = signature_data
        application.agreement_signed = True
        application.agreement_signed_at = timezone.now()
        application.signature_ip = get_client_ip(request)
        application.status = 'signed'
        application.save()
        
        # Create or update contributor profile
        contributor, created = Contributor.objects.get_or_create(
            user=request.user,
            defaults={
                'application': application,
                'daily_upload_limit': 10,
                'is_active': True
            }
        )
        
        if not created:
            contributor.application = application
            contributor.is_active = True
            contributor.save()
        
        messages.success(request, 'Agreement signed successfully! You can now upload books.')
        return redirect('books:contributor_dashboard')
    
    context = {
        'application': application,
        'agreement': agreement,
    }
    return render(request, 'books/sign_agreement.html', context)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
@login_required


@login_required
def earnings_dashboard(request):
    """Earnings dashboard for contributors to track their earnings and book status"""
    
    try:
        # Check if user is a contributor
        contributor = Contributor.objects.get(user=request.user, is_active=True)
        
        # Get all books by this contributor
        books = Book.objects.filter(contributor=contributor).order_by('-created_at')
        
        # Calculate statistics
        total_books = books.count()
        approved_books = books.filter(is_active=True).count()
        pending_books = books.filter(is_active=False).count()
        
        # Calculate earnings
        total_earnings = ContributorEarning.objects.filter(contributor=contributor).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Get earnings by month
        from django.db import connection
        earnings_by_month = ContributorEarning.objects.filter(
            contributor=contributor
        ).extra(
            select={'month': "strftime('%%Y-%%m', created_at)"}
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('-month')
        
        # Get recent earnings
        recent_earnings = ContributorEarning.objects.filter(
            contributor=contributor
        ).select_related('book').order_by('-created_at')[:10]
        
        # Calculate this month's earnings
        from django.utils import timezone
        current_month = timezone.now().month
        current_year = timezone.now().year
        this_month_earnings = ContributorEarning.objects.filter(
            contributor=contributor,
            created_at__year=current_year,
            created_at__month=current_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate percentage change
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        last_month_earnings = ContributorEarning.objects.filter(
            contributor=contributor,
            created_at__year=last_month_year,
            created_at__month=last_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        if last_month_earnings > 0:
            earnings_change = ((this_month_earnings - last_month_earnings) / last_month_earnings) * 100
        else:
            earnings_change = 100 if this_month_earnings > 0 else 0
        
        context = {
            'contributor': contributor,
            'books': books,
            'total_books': total_books,
            'approved_books': approved_books,
            'pending_books': pending_books,
            'total_earnings': total_earnings,
            'available_balance': contributor.available_balance,
            'recent_earnings': recent_earnings,
            'approved_books_list': books.filter(is_active=True),
            'pending_books_list': books.filter(is_active=False),
            'earnings_by_month': earnings_by_month,
            'this_month_earnings': this_month_earnings,
            'earnings_change': earnings_change,
            'total_downloads': sum(book.downloads_count for book in books),
        }
        
        return render(request, 'books/earnings_dashboard.html', context)
        
    except Contributor.DoesNotExist:
        messages.error(request, 'You are not a registered contributor.')
        return redirect('books:contributor_dashboard')
@login_required
def request_withdrawal(request):
    """Request withdrawal of earnings"""
    contributor = get_object_or_404(Contributor, user=request.user)
    
    # Check withdrawal eligibility
    can_withdraw, message = contributor.can_withdraw()
    if not can_withdraw:
        messages.error(request, message)
        return redirect('books:contributor_dashboard')
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        payment_details = request.POST.get('payment_details')
        
        if not all([amount, payment_method, payment_details]):
            messages.error(request, 'Please fill all fields.')
            return redirect('books:request_withdrawal')
        
        amount = float(amount)
        if amount < 250:
            messages.error(request, 'Minimum withdrawal amount is K250.')
            return redirect('books:request_withdrawal')
        
        if amount > float(contributor.available_balance):
            messages.error(request, 'Insufficient balance.')
            return redirect('books:request_withdrawal')
        
        # Create withdrawal request
        withdrawal = ContributorWithdrawal.objects.create(
            contributor=contributor,
            amount=amount,
            payment_method=payment_method,
            payment_details=payment_details,
            status='pending'
        )
        
        # Deduct from available balance
        contributor.available_balance -= amount
        contributor.pending_withdrawal += amount
        contributor.save()
        
        messages.success(request, f'Withdrawal request of K{amount} submitted successfully!')
        return redirect('books:contributor_dashboard')
    
    context = {
        'contributor': contributor,
        'payment_methods': ContributorWithdrawal.PAYMENT_METHODS,
        'min_amount': 250,
        'max_amount': contributor.available_balance,
    }
    return render(request, 'books/request_withdrawal.html', context)


@staff_member_required
def manage_applications(request):
    """Admin view to manage contributor applications"""
    applications = ContributorApplication.objects.all().order_by('-created_at')
    pending_apps = applications.filter(status='pending')
    approved_apps = applications.filter(status='approved')
    rejected_apps = applications.filter(status='rejected')
    
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        action = request.POST.get('action')
        notes = request.POST.get('admin_notes', '')
        
        application = get_object_or_404(ContributorApplication, id=app_id)
        
        if action == 'approve':
            application.status = 'approved'
            application.admin_notes = notes
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save()
            messages.success(request, f'Application from {application.user.username} approved.')
        elif action == 'reject':
            application.status = 'rejected'
            application.admin_notes = notes
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save()
            messages.success(request, f'Application from {application.user.username} rejected.')
        
        return redirect('books:manage_applications')
    
    context = {
        'applications': applications,
        'pending_apps': pending_apps,
        'approved_apps': approved_apps,
        'rejected_apps': rejected_apps,
    }
    return render(request, 'books/manage_applications.html', context)


@staff_member_required
def manage_withdrawals(request):
    """Admin view to manage withdrawal requests"""
    withdrawals = ContributorWithdrawal.objects.all().order_by('-created_at')
    pending_withdrawals = withdrawals.filter(status='pending')
    
    if request.method == 'POST':
        withdrawal_id = request.POST.get('withdrawal_id')
        action = request.POST.get('action')
        
        withdrawal = get_object_or_404(ContributorWithdrawal, id=withdrawal_id)
        
        if action == 'complete':
            withdrawal.status = 'completed'
            withdrawal.processed_by = request.user
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
            
            # Update contributor
            withdrawal.contributor.pending_withdrawal -= withdrawal.amount
            withdrawal.contributor.save()
            
            messages.success(request, f'Withdrawal of K{withdrawal.amount} marked as completed.')
        elif action == 'fail':
            withdrawal.status = 'failed'
            withdrawal.admin_notes = request.POST.get('notes', '')
            withdrawal.save()
            
            # Refund the amount
            withdrawal.contributor.available_balance += withdrawal.amount
            withdrawal.contributor.pending_withdrawal -= withdrawal.amount
            withdrawal.contributor.save()
            
            messages.warning(request, f'Withdrawal of K{withdrawal.amount} marked as failed.')
        
        return redirect('books:manage_withdrawals')
    
    context = {
        'withdrawals': withdrawals,
        'pending_withdrawals': pending_withdrawals,
    }
    return render(request, 'books/manage_withdrawals.html', context)
@staff_member_required
def get_application_details(request, app_id):
    """Get application details as JSON"""
    app = get_object_or_404(ContributorApplication, id=app_id)
    data = {
        'id': app.id,
        'full_name': app.full_name,
        'username': app.user.username,
        'email': app.email,
        'phone_number': app.phone_number,
        'address': app.address,
        'subject_specialization': app.subject_specialization,
        'teaching_experience': app.teaching_experience,
        'writing_experience': app.writing_experience,
        'reason_to_contribute': app.reason_to_contribute,
        'grade12_certificate': app.grade12_certificate.url if app.grade12_certificate else None,
        'nrc_document': app.nrc_document.url if app.nrc_document else None,
        'status': app.status,
        'created_at': app.created_at.isoformat(),
    }
    return JsonResponse(data)

# Add these imports at the top of books/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from downloads.models import BookDownload, UserDownloadLimit
from .models import Category, GradeLevel, Language

@staff_member_required
def manage_users(request):
    """Admin view to manage users"""
    users = User.objects.all().order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    try:
        users_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        users_page = paginator.page(1)
    
    # Get user download counts
    for user in users_page:
        user.total_downloads = BookDownload.objects.filter(user=user).count()
    
    context = {
        'users': users_page,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'premium_users': User.objects.filter(user_type='premium').count(),
        'lifetime_users': User.objects.filter(user_type='lifetime').count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
    }
    return render(request, 'admin/manage_users.html', context)


@staff_member_required
def manage_categories(request):
    """Admin view to manage categories"""
    categories = Category.objects.all().order_by('order', 'name')
    
    for cat in categories:
        cat.book_count = Book.objects.filter(category=cat, is_active=True).count()
    
    context = {
        'categories': categories,
        'active_count': categories.filter(is_active=True).count(),
        'inactive_count': categories.filter(is_active=False).count(),
        'total_books': Book.objects.filter(is_active=True).count(),
    }
    return render(request, 'admin/manage_categories.html', context)
@staff_member_required
def manage_grades(request):
    """Admin view to manage grade levels"""
    grades = GradeLevel.objects.all().order_by('order', 'name')
    
    for grade in grades:
        grade.book_count = Book.objects.filter(grade_level=grade, is_active=True).count()
    
    context = {'grades': grades}
    return render(request, 'admin/manage_grade_levels.html', context)


@staff_member_required
def manage_languages(request):
    """Admin view to manage languages"""
    languages = Language.objects.all().order_by('order', 'name')
    
    for lang in languages:
        lang.book_count = Book.objects.filter(language=lang, is_active=True).count()
    
    context = {'languages': languages}
    return render(request, 'admin/manage_languages.html', context)


@staff_member_required
def manage_downloads(request):
    """Admin view to manage download records"""
    records = BookDownload.objects.all().order_by('-downloaded_at')
    
    # Pagination
    paginator = Paginator(records, 30)
    page = request.GET.get('page', 1)
    try:
        records_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        records_page = paginator.page(1)
    
    # Get statistics
    today = timezone.now().date()
    today_downloads = BookDownload.objects.filter(downloaded_at__date=today).count()
    unique_users = BookDownload.objects.values('user').distinct().count()
    
    # Calculate average daily downloads (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    last_30_days = BookDownload.objects.filter(downloaded_at__date__gte=thirty_days_ago).count()
    avg_daily = round(last_30_days / 30, 1) if last_30_days > 0 else 0
    
    context = {
        'records': records_page,
        'total_downloads': BookDownload.objects.count(),
        'today_downloads': today_downloads,
        'unique_users': unique_users,
        'avg_daily': avg_daily,
    }
    return render(request, 'admin/manage_download_records.html', context)


from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
from accounts.models import User
from downloads.models import UserDownloadLimit, BookDownload
from django.utils import timezone
from datetime import timedelta

@staff_member_required
def manage_limits(request):
    """View for managing user download limits"""
    
    # Get all users with their download limits
    users = User.objects.all().order_by('-date_joined')
    
    # Get or create download limits for each user
    user_data = []
    for user in users:
        # Get or create download limit
        limit, created = UserDownloadLimit.objects.get_or_create(
            user=user,
            defaults={
                'subscription_tier': 'basic',
                'daily_limit': 20,
                'monthly_limit': 500
            }
        )
        
        # Calculate download counts
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        today_downloads = BookDownload.objects.filter(
            user=user,
            downloaded_at__date=today
        ).count()
        
        month_downloads = BookDownload.objects.filter(
            user=user,
            downloaded_at__date__gte=start_of_month
        ).count()
        
        total_downloads = BookDownload.objects.filter(user=user).count()
        
        # Update limit object with current counts
        limit.downloads_today = today_downloads
        limit.downloads_this_month = month_downloads
        limit.downloads_total = total_downloads
        limit.save()
        
        user_data.append({
            'user': user,
            'limit': limit,
            'today_downloads': today_downloads,
            'month_downloads': month_downloads,
            'total_downloads': total_downloads,
            'remaining_today': max(0, (limit.daily_limit or 0) - today_downloads) if limit.daily_limit else 'Unlimited',
            'remaining_month': max(0, (limit.monthly_limit or 0) - month_downloads) if limit.monthly_limit else 'Unlimited',
        })
    
    # Pagination
    paginator = Paginator(user_data, 20)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    # Statistics
    total_users = users.count()
    premium_users = users.filter(user_type='premium').count()
    lifetime_users = users.filter(user_type='lifetime').count()
    basic_users = users.filter(user_type='basic').count()
    
    # Total downloads this month
    start_of_month = timezone.now().date().replace(day=1)
    total_month_downloads = BookDownload.objects.filter(
        downloaded_at__date__gte=start_of_month
    ).count()
    
    context = {
        'users': users_page,
        'total_users': total_users,
        'premium_users': premium_users,
        'lifetime_users': lifetime_users,
        'basic_users': basic_users,
        'total_month_downloads': total_month_downloads,
    }
    
    return render(request, 'admin/manage_user_limits.html', context)

@staff_member_required
def get_application_details(request, app_id):
    """Get application details via AJAX"""
    from .models import ContributorApplication
    
    app = get_object_or_404(ContributorApplication, id=app_id)
    
    data = {
        'id': app.id,
        'full_name': app.full_name,
        'username': app.user.username,
        'email': app.email,
        'phone_number': app.phone_number,
        'address': app.address,
        'subject_specialization': app.subject_specialization,
        'teaching_experience': app.teaching_experience,
        'writing_experience': app.writing_experience,
        'reason_to_contribute': app.reason_to_contribute,
        'grade12_certificate': app.grade12_certificate.url if app.grade12_certificate else None,
        'nrc_document': app.nrc_document.url if app.nrc_document else None,
        'status': app.status,
        'admin_notes': app.admin_notes,
        'created_at': app.created_at.isoformat(),
    }
    
    return JsonResponse(data)
@staff_member_required
def reset_user_limit(request, user_id):
    """Reset download limit for a specific user"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        limit, created = UserDownloadLimit.objects.get_or_create(user=user)
        
        # Reset counts
        limit.downloads_today = 0
        limit.downloads_this_month = 0
        limit.save()
        
        messages.success(request, f'Download limits reset for {user.username}')
        return redirect('books:manage_limits')
    
    return redirect('books:manage_limits')


@staff_member_required
def reset_all_limits(request):
    """Reset all user download limits"""
    if request.method == 'POST':
        UserDownloadLimit.objects.update(
            downloads_today=0,
            downloads_this_month=0
        )
        messages.success(request, 'All download limits have been reset')
        return redirect('books:manage_limits')
    
    return redirect('books:manage_limits')

@staff_member_required
def manage_users(request):
    """Admin view to manage users"""
    users = User.objects.all().order_by('-date_joined')
    
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    try:
        users_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        users_page = paginator.page(1)
    
    for user in users_page:
        user.total_downloads = BookDownload.objects.filter(user=user).count()
    
    context = {
        'users': users_page,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'premium_users': User.objects.filter(user_type='premium').count(),
        'lifetime_users': User.objects.filter(user_type='lifetime').count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
    }
    return render(request, 'admin/manage_users.html', context)
# API endpoints for AJAX operations
@staff_member_required
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required
def add_category(request):
    """Add new category"""
    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.POST.get('icon', 'book')
        description = request.POST.get('description', '')
        order = request.POST.get('order', 0)
        
        Category.objects.create(
            name=name,
            icon=icon,
            description=description,
            order=order,
            is_active=True
        )
        messages.success(request, 'Category added successfully!')
    return redirect('books:manage_categories')


@staff_member_required
def edit_category(request, category_id):
    """Get category data for editing"""
    category = get_object_or_404(Category, id=category_id)
    return JsonResponse({
        'id': category.id,
        'name': category.name,
        'icon': category.icon,
        'description': category.description,
        'order': category.order,
    })


@staff_member_required
def update_category(request, category_id):
    """Update category"""
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        category.name = request.POST.get('name')
        category.icon = request.POST.get('icon', 'book')
        category.description = request.POST.get('description', '')
        category.order = request.POST.get('order', 0)
        category.save()
        messages.success(request, 'Category updated successfully!')
    return redirect('books:manage_categories')


@staff_member_required
def delete_category(request, category_id):
    """Delete category"""
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        category.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


# Similar endpoints for grades and languages...
@staff_member_required
def add_grade(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        order = request.POST.get('order', 0)
        is_active = request.POST.get('is_active') == 'on'
        GradeLevel.objects.create(name=name, order=order, is_active=is_active)
        messages.success(request, 'Grade level added successfully!')
    return redirect('books:manage_grades')


@staff_member_required
def add_language(request):
    """Add new language"""
    if request.method == 'POST':
        name = request.POST.get('name')
        native_name = request.POST.get('native_name', '')
        code = request.POST.get('code')
        order = request.POST.get('order', 0)
        is_active = request.POST.get('is_active') == 'on'
        
        Language.objects.create(
            name=name,
            native_name=native_name,
            code=code,
            order=order,
            is_active=is_active
        )
        messages.success(request, f'Language "{name}" added successfully!')
    return redirect('books:manage_languages')


@staff_member_required
def reset_user_limit(request, user_id):
    """Reset user daily download limit"""
    if request.method == 'POST':
        limit, created = UserDownloadLimit.objects.get_or_create(user_id=user_id)
        limit.downloads_today = 0
        limit.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required
def reset_all_limits(request):
    """Reset all users daily download limits"""
    if request.method == 'POST':
        UserDownloadLimit.objects.update(downloads_today=0)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required
def export_downloads(request):
    """Export download records to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="downloads_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['User', 'Book', 'IP Address', 'Date', 'Type'])
    
    downloads = BookDownload.objects.select_related('book', 'user').order_by('-downloaded_at')
    for d in downloads:
        writer.writerow([
            d.user.username if d.user else 'Anonymous',
            d.book.title,
            d.ip_address,
            d.downloaded_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Premium' if d.is_premium else 'Free'
        ])
    
    return response
@staff_member_required
def edit_grade(request, grade_id):
    """Get grade data for editing"""
    grade = get_object_or_404(GradeLevel, id=grade_id)
    return JsonResponse({
        'id': grade.id,
        'name': grade.name,
        'order': grade.order,
        'is_active': grade.is_active,
    })


@staff_member_required
def update_grade(request, grade_id):
    """Update grade"""
    if request.method == 'POST':
        grade = get_object_or_404(GradeLevel, id=grade_id)
        grade.name = request.POST.get('name')
        grade.order = request.POST.get('order', 0)
        grade.is_active = request.POST.get('is_active') == 'on'
        grade.save()
        messages.success(request, 'Grade level updated successfully!')
    return redirect('books:manage_grades')


@staff_member_required
def delete_grade(request, grade_id):
    """Delete grade"""
    if request.method == 'POST':
        grade = get_object_or_404(GradeLevel, id=grade_id)
        grade.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required
def edit_language(request, lang_id):
    """Get language data for editing"""
    lang = get_object_or_404(Language, id=lang_id)
    return JsonResponse({
        'id': lang.id,
        'name': lang.name,
        'native_name': lang.native_name,
        'code': lang.code,
        'order': lang.order,
        'is_active': lang.is_active,
    })


@staff_member_required
def update_language(request, lang_id):
    """Update language"""
    if request.method == 'POST':
        lang = get_object_or_404(Language, id=lang_id)
        lang.name = request.POST.get('name')
        lang.native_name = request.POST.get('native_name', '')
        lang.code = request.POST.get('code')
        lang.order = request.POST.get('order', 0)
        lang.save()
        messages.success(request, 'Language updated successfully!')
    return redirect('books:manage_languages')


@staff_member_required
def delete_language(request, lang_id):
    """Delete language"""
    if request.method == 'POST':
        lang = get_object_or_404(Language, id=lang_id)
        lang.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@staff_member_required
def get_download_counts(request):
    """Get download counts for all users (AJAX)"""
    from downloads.models import BookDownload
    counts = {}
    users = User.objects.all()
    for user in users:
        counts[user.id] = BookDownload.objects.filter(user=user).count()
    return JsonResponse(counts)


@staff_member_required
def add_category(request):
    """Add new category via AJAX"""
    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.POST.get('icon', 'book')
        description = request.POST.get('description', '')
        order = request.POST.get('order', 0)
        
        category = Category.objects.create(
            name=name,
            icon=icon,
            description=description,
            order=order,
            is_active=True
        )
        messages.success(request, f'Category "{name}" added successfully!')
        return redirect('books:manage_categories')
    return redirect('books:manage_categories')


@staff_member_required
def edit_category(request, category_id):
    """Get category data for editing (AJAX)"""
    category = get_object_or_404(Category, id=category_id)
    return JsonResponse({
        'id': category.id,
        'name': category.name,
        'icon': category.icon,
        'description': category.description,
        'order': category.order,
    })


@staff_member_required
def update_category(request, category_id):
    """Update category"""
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        category.name = request.POST.get('name')
        category.icon = request.POST.get('icon', 'book')
        category.description = request.POST.get('description', '')
        category.order = request.POST.get('order', 0)
        category.save()
        messages.success(request, f'Category "{category.name}" updated successfully!')
    return redirect('books:manage_categories')


@staff_member_required
def delete_category(request, category_id):
    """Delete category via AJAX"""
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id)
        category.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required
def add_grade(request):
    """Add new grade level"""
    if request.method == 'POST':
        name = request.POST.get('name')
        order = request.POST.get('order', 0)
        is_active = request.POST.get('is_active') == 'on'
        
        GradeLevel.objects.create(name=name, order=order, is_active=is_active)
        messages.success(request, f'Grade level "{name}" added successfully!')
    return redirect('books:manage_grades')


@staff_member_required
def edit_grade(request, grade_id):
    """Get grade data for editing (AJAX)"""
    grade = get_object_or_404(GradeLevel, id=grade_id)
    return JsonResponse({
        'id': grade.id,
        'name': grade.name,
        'order': grade.order,
        'is_active': grade.is_active,
    })


@staff_member_required
def update_grade(request, grade_id):
    """Update grade level"""
    if request.method == 'POST':
        grade = get_object_or_404(GradeLevel, id=grade_id)
        grade.name = request.POST.get('name')
        grade.order = request.POST.get('order', 0)
        grade.is_active = request.POST.get('is_active') == 'on'
        grade.save()
        messages.success(request, f'Grade level "{grade.name}" updated successfully!')
    return redirect('books:manage_grades')


@staff_member_required
def delete_grade(request, grade_id):
    """Delete grade level via AJAX"""
    if request.method == 'POST':
        grade = get_object_or_404(GradeLevel, id=grade_id)
        grade.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required
def add_language(request):
    """Add new language"""
    if request.method == 'POST':
        name = request.POST.get('name')
        native_name = request.POST.get('native_name', '')
        code = request.POST.get('code')
        order = request.POST.get('order', 0)
        
        Language.objects.create(
            name=name,
            native_name=native_name,
            code=code,
            order=order,
            is_active=True
        )
        messages.success(request, f'Language "{name}" added successfully!')
    return redirect('books:manage_languages')


@staff_member_required
def edit_language(request, lang_id):
    """Get language data for editing (AJAX)"""
    lang = get_object_or_404(Language, id=lang_id)
    return JsonResponse({
        'id': lang.id,
        'name': lang.name,
        'native_name': lang.native_name,
        'code': lang.code,
        'order': lang.order,
    })


@staff_member_required
def update_language(request, lang_id):
    """Update language"""
    if request.method == 'POST':
        lang = get_object_or_404(Language, id=lang_id)
        lang.name = request.POST.get('name')
        lang.native_name = request.POST.get('native_name', '')
        lang.code = request.POST.get('code')
        lang.order = request.POST.get('order', 0)
        lang.save()
        messages.success(request, f'Language "{lang.name}" updated successfully!')
    return redirect('books:manage_languages')


@staff_member_required
def delete_language(request, lang_id):
    """Delete language via AJAX"""
    if request.method == 'POST':
        lang = get_object_or_404(Language, id=lang_id)
        lang.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required
def toggle_user_status(request, user_id):
    """Toggle user active status via AJAX"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({'success': True, 'is_active': user.is_active})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required
def reset_user_limit(request, user_id):
    """Reset user daily download limit via AJAX"""
    if request.method == 'POST':
        from downloads.models import UserDownloadLimit
        limit, created = UserDownloadLimit.objects.get_or_create(user_id=user_id)
        limit.downloads_today = 0
        limit.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required
def reset_all_limits(request):
    """Reset all users daily download limits via AJAX"""
    if request.method == 'POST':
        from downloads.models import UserDownloadLimit
        UserDownloadLimit.objects.update(downloads_today=0)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@staff_member_required
def export_downloads(request):
    """Export download records to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="downloads_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['User', 'Book', 'IP Address', 'Date', 'Type'])
    
    downloads = BookDownload.objects.select_related('book', 'user').order_by('-downloaded_at')
    for d in downloads:
        writer.writerow([
            d.user.username if d.user else 'Anonymous',
            d.book.title,
            d.ip_address,
            d.downloaded_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Premium' if d.is_premium else 'Free'
        ])
    
    return response

@staff_member_required
def edit_category(request, category_id):
    """Get category data for editing (AJAX)"""
    category = get_object_or_404(Category, id=category_id)
    return JsonResponse({
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'icon': category.icon,
        'description': category.description,
        'order': category.order,
        'is_active': category.is_active,
        'created_at': category.created_at.isoformat(),
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from .models import GradeLevel, Category, Language
from django.utils.text import slugify

# ============ GRADE LEVEL MANAGEMENT VIEWS ============

@staff_member_required
def manage_grades(request):
    """View for managing grade levels"""
    grades = GradeLevel.objects.filter().order_by('order')
    
    context = {
        'grades': grades,
        'title': 'Manage Grade Levels',
    }
    return render(request, 'admin/manage_grade_levels.html', context)


@staff_member_required
def add_grade(request):
    """Add a new grade level"""
    if request.method == 'POST':
        name = request.POST.get('name')
        order = request.POST.get('order', 0)
        
        if not name:
            messages.error(request, 'Grade name is required')
            return redirect('books:manage_grades')
        
        # Check if grade already exists
        if GradeLevel.objects.filter(name__iexact=name).exists():
            messages.error(request, f'Grade "{name}" already exists')
            return redirect('books:manage_grades')
        
        # Create new grade
        grade = GradeLevel.objects.create(
            name=name,
            order=int(order),
            is_active=True
        )
        
        messages.success(request, f'Grade "{grade.name}" has been added successfully!')
        return redirect('books:manage_grades')
    
    return redirect('books:manage_grades')


@staff_member_required
def edit_grade(request, grade_id):
    """Edit grade level form view"""
    grade = get_object_or_404(GradeLevel, id=grade_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        order = request.POST.get('order', grade.order)
        
        if not name:
            messages.error(request, 'Grade name is required')
            return redirect('books:manage_grades')
        
        # Check if name already exists (excluding current grade)
        if GradeLevel.objects.exclude(id=grade_id).filter(name__iexact=name).exists():
            messages.error(request, f'Grade "{name}" already exists')
            return redirect('books:manage_grades')
        
        grade.name = name
        grade.order = int(order)
        grade.save()
        
        messages.success(request, f'Grade "{grade.name}" has been updated successfully!')
        return redirect('books:manage_grades')
    
    context = {
        'grade': grade,
        'title': f'Edit Grade: {grade.name}',
    }
    return render(request, 'admin/edit_grade.html', context)


@staff_member_required
def update_grade(request, grade_id):
    """Update grade via AJAX"""
    if request.method == 'POST':
        grade = get_object_or_404(GradeLevel, id=grade_id)
        name = request.POST.get('name')
        order = request.POST.get('order')
        
        if name:
            grade.name = name
        if order:
            grade.order = int(order)
        
        grade.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Grade updated successfully'})
        
        messages.success(request, 'Grade updated successfully')
        return redirect('books:manage_grades')
    
    return redirect('books:manage_grades')


@staff_member_required
def delete_grade(request, grade_id):
    """Delete a grade level"""
    if request.method == 'POST':
        grade = get_object_or_404(GradeLevel, id=grade_id)
        grade_name = grade.name
        
        # Check if grade has associated books
        if grade.books.exists():
            messages.error(request, f'Cannot delete "{grade_name}" because it has associated books.')
            return redirect('books:manage_grades')
        
        grade.delete()
        messages.success(request, f'Grade "{grade_name}" has been deleted successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Grade deleted successfully'})
        
        return redirect('books:manage_grades')
    
    return redirect('books:manage_grades')


# ============ LANGUAGE MANAGEMENT VIEWS ============

@staff_member_required
def manage_languages(request):
    """View for managing languages"""
    languages = Language.objects.filter().order_by('order')
    
    context = {
        'languages': languages,
        'title': 'Manage Languages',
    }
    return render(request, 'admin/manage_languages.html', context)


@staff_member_required
def add_language(request):
    """Add a new language"""
    if request.method == 'POST':
        name = request.POST.get('name')
        native_name = request.POST.get('native_name', '')
        code = request.POST.get('code')
        icon = request.POST.get('icon', 'language')
        order = request.POST.get('order', 0)
        
        if not name or not code:
            messages.error(request, 'Language name and code are required')
            return redirect('books:manage_languages')
        
        # Check if language already exists
        if Language.objects.filter(name__iexact=name).exists():
            messages.error(request, f'Language "{name}" already exists')
            return redirect('books:manage_languages')
        
        # Create new language
        language = Language.objects.create(
            name=name,
            native_name=native_name,
            code=code.upper(),
            icon=icon,
            order=int(order),
            is_active=True
        )
        
        messages.success(request, f'Language "{language.name}" has been added successfully!')
        return redirect('books:manage_languages')
    
    return redirect('books:manage_languages')


@staff_member_required
def edit_language(request, language_id):
    """Edit language form view"""
    language = get_object_or_404(Language, id=language_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        native_name = request.POST.get('native_name', '')
        code = request.POST.get('code')
        icon = request.POST.get('icon', language.icon)
        order = request.POST.get('order', language.order)
        
        if not name or not code:
            messages.error(request, 'Language name and code are required')
            return redirect('books:manage_languages')
        
        language.name = name
        language.native_name = native_name
        language.code = code.upper()
        language.icon = icon
        language.order = int(order)
        language.save()
        
        messages.success(request, f'Language "{language.name}" has been updated successfully!')
        return redirect('books:manage_languages')
    
    context = {
        'language': language,
        'title': f'Edit Language: {language.name}',
    }
    return render(request, 'admin/edit_language.html', context)


@staff_member_required
def update_language(request, language_id):
    """Update language via AJAX"""
    if request.method == 'POST':
        language = get_object_or_404(Language, id=language_id)
        name = request.POST.get('name')
        code = request.POST.get('code')
        order = request.POST.get('order')
        
        if name:
            language.name = name
        if code:
            language.code = code.upper()
        if order:
            language.order = int(order)
        
        language.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Language updated successfully'})
        
        messages.success(request, 'Language updated successfully')
        return redirect('books:manage_languages')
    
    return redirect('books:manage_languages')


@staff_member_required
def delete_language(request, language_id):
    """Delete a language"""
    if request.method == 'POST':
        language = get_object_or_404(Language, id=language_id)
        language_name = language.name
        
        # Check if language has associated books
        if language.books.exists():
            messages.error(request, f'Cannot delete "{language_name}" because it has associated books.')
            return redirect('books:manage_languages')
        
        language.delete()
        messages.success(request, f'Language "{language_name}" has been deleted successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Language deleted successfully'})
        
        return redirect('books:manage_languages')
    
    return redirect('books:manage_languages')