from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from books.models import Book, Category, GradeLevel, Language
from .models import BookDownload, BookView, BookReadOnline, UserDownloadLimit
import json
from django.http import JsonResponse


# ==================== VIEW TRACKING ====================

def track_book_view(request, slug):
    """Track when a book is viewed"""
    try:
        book = get_object_or_404(Book, slug=slug, is_active=True)
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Create view record
        BookView.objects.create(
            book=book,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip_address
        )
        
        # Increment book view count
        book.views_count += 1
        book.save(update_fields=['views_count'])
        
        return True
    except Exception as e:
        print(f"Error tracking view: {e}")
        return False


@require_POST
@csrf_exempt
def track_view_ajax(request, slug):
    """Track book view via AJAX"""
    try:
        book = get_object_or_404(Book, slug=slug, is_active=True)
        book.views_count += 1
        book.save(update_fields=['views_count'])
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ==================== DOWNLOAD FUNCTIONS ====================

@login_required
def download_book(request, slug):
    """Handle book download"""
    book = get_object_or_404(Book, slug=slug, is_active=True)
    
    # Check if book has PDF file
    if not book.pdf_file:
        messages.error(request, "This book has no downloadable file available.")
        return redirect('books:book_detail', slug=book.slug)
    
    # Check user download limits
    user_limit, created = UserDownloadLimit.objects.get_or_create(
        user=request.user,
        defaults={'daily_limit': 20, 'monthly_limit': 500}
    )
    
    if not user_limit.can_download():
        messages.error(request, "You have reached your daily download limit. Upgrade to Premium for unlimited downloads!")
        return redirect('books:book_detail', slug=book.slug)
    
    # Check if book is free or user has purchased
    if not book.is_free:
        # Check if user has purchased or has premium subscription
        if request.user.user_type in ['premium', 'lifetime']:
            pass  # Premium users can download
        elif request.user.credits_balance >= book.price:
            # Deduct credits
            request.user.credits_balance -= book.price
            request.user.save()
        else:
            messages.error(request, f"Insufficient credits. This book costs K{book.price}. Please add credits or upgrade to Premium.")
            return redirect('books:book_detail', slug=book.slug)
    
    # Track download
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    
    BookDownload.objects.create(
        book=book,
        user=request.user,
        ip_address=ip_address,
        is_premium=request.user.user_type in ['premium', 'lifetime']
    )
    
    # Increment download count
    book.downloads_count += 1
    book.save(update_fields=['downloads_count'])
    
    # Increment user download count
    user_limit.increment_download()
    
    # Serve the file
    try:
        response = FileResponse(open(book.pdf_file.path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{book.slug}.pdf"'
        return response
    except FileNotFoundError:
        messages.error(request, "The file was not found.")
        return redirect('books:book_detail', slug=book.slug)


# ==================== READ ONLINE ====================

def read_online(request, slug):
    """Read book online (PDF viewer)"""
    try:
        # Get the book
        book = get_object_or_404(Book, slug=slug, is_active=True)
        
        # Check if book has PDF file
        if not book.pdf_file:
            messages.error(request, "This book has no PDF file available for online reading.")
            return redirect('books:book_detail', slug=book.slug)
        
        # Track view (don't let errors break the page)
        try:
            track_book_view(request, slug)
        except Exception as e:
            print(f"View tracking failed: {e}")
        
        # Track online reading session
        reading_session = None
        try:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Get or create reading session
            reading_session, created = BookReadOnline.objects.get_or_create(
                book=book,
                user=request.user if request.user.is_authenticated else None,
                ip_address=ip_address,
                defaults={
                    'started_at': timezone.now(),
                    'total_pages': book.pages or 0
                }
            )
        except Exception as e:
            print(f"Reading session tracking failed: {e}")
        
        context = {
            'book': book,
            'reading_session': reading_session,
        }
        return render(request, 'downloads/read_online.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading book: {str(e)}")
        return redirect('books:book_list')


# ==================== USER HISTORY ====================

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import BookDownload, BookReadOnline
from books.models import Book

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import BookDownload, BookReadOnline
from books.models import Book

@login_required
def my_downloads(request):
    """View user's download history with enhanced statistics and pagination"""
    
    # Get all downloads for the user
    downloads = BookDownload.objects.filter(
        user=request.user
    ).select_related('book', 'book__category').order_by('-downloaded_at')
    
    # Calculate statistics
    total_downloads = downloads.count()
    
    # Calculate total storage used
    total_size = 0
    for download in downloads[:50]:
        if download.book.file_size:
            total_size += download.book.file_size
    total_size_mb = round(total_size / (1024 * 1024), 2) if total_size > 0 else 0
    
    # Get most downloaded book - Using Python method for reliability
    most_downloaded_title = None
    most_downloaded_slug = None
    most_downloaded_count = 0
    
    if total_downloads > 0:
        # Count downloads per book
        book_counts = {}
        for download in downloads:
            title = download.book.title
            slug = download.book.slug
            if title in book_counts:
                book_counts[title]['count'] += 1
            else:
                book_counts[title] = {
                    'slug': slug,
                    'count': 1
                }
        
        # Find the book with highest count
        if book_counts:
            most_downloaded_title = max(book_counts, key=lambda x: book_counts[x]['count'])
            most_downloaded_slug = book_counts[most_downloaded_title]['slug']
            most_downloaded_count = book_counts[most_downloaded_title]['count']
    
    # Get last download date
    last_download = downloads.order_by('-downloaded_at').first()
    last_download_date = last_download.downloaded_at.strftime('%b %d, %Y') if last_download else None
    
    # Get download trends (last 7 days)
    today = timezone.now().date()
    weekly_trends = []
    max_weekly_count = 0
    
    for i in range(6, -1, -1):
        day_date = today - timedelta(days=i)
        day_count = downloads.filter(downloaded_at__date=day_date).count()
        weekly_trends.append({
            'day': day_date.strftime('%a'),
            'count': day_count,
            'full_date': day_date.strftime('%Y-%m-%d')
        })
        if day_count > max_weekly_count:
            max_weekly_count = day_count
    
    # Calculate weekly total and average
    weekly_total = sum(day['count'] for day in weekly_trends)
    weekly_average = round(weekly_total / 7, 1) if weekly_total > 0 else 0
    
    # Get category distribution
    category_distribution = {}
    for download in downloads:
        category_name = download.book.category.name if download.book.category else 'Uncategorized'
        category_distribution[category_name] = category_distribution.get(category_name, 0) + 1
    
    # Prepare category data for chart
    category_labels = list(category_distribution.keys())
    category_data = list(category_distribution.values())
    
    # Get monthly download count
    current_month = today.month
    current_year = today.year
    monthly_downloads = downloads.filter(
        downloaded_at__year=current_year,
        downloaded_at__month=current_month
    ).count()
    
    # Get all-time favorite category
    favorite_category = None
    if category_labels:
        max_count_index = category_data.index(max(category_data))
        favorite_category = category_labels[max_count_index]
    
    # Get recommended books based on download history
    recommended_books = []
    if total_downloads > 0:
        # Get categories the user downloads most
        user_categories = downloads.values_list('book__category', flat=True).distinct()[:3]
        recommended_books = Book.objects.filter(
            is_active=True,
            category__in=user_categories,
            is_free=True
        ).exclude(
            id__in=downloads.values_list('book__id', flat=True)
        ).distinct()[:4]
    else:
        # No downloads, recommend popular free books
        recommended_books = Book.objects.filter(
            is_active=True,
            is_free=True,
            is_featured=True
        )[:4]
        if not recommended_books:
            recommended_books = Book.objects.filter(is_active=True, is_free=True)[:4]
    
    # Pagination
    paginator = Paginator(downloads, 12)
    page = request.GET.get('page', 1)
    
    try:
        downloads_page = paginator.page(page)
    except PageNotAnInteger:
        downloads_page = paginator.page(1)
    except EmptyPage:
        downloads_page = paginator.page(paginator.num_pages)
    
    # Get reading progress for each downloaded book
    for download in downloads_page:
        read_session = BookReadOnline.objects.filter(
            user=request.user,
            book=download.book
        ).first()
        download.read_progress = read_session.completion_percentage if read_session else 0
        download.file_size_mb = round(download.book.file_size / (1024 * 1024), 2) if download.book.file_size > 0 else 0
    
    context = {
        'downloads': downloads_page,
        'total_downloads': total_downloads,
        'total_size': total_size_mb,
        'most_downloaded_title': most_downloaded_title,
        'most_downloaded_slug': most_downloaded_slug,
        'most_downloaded_count': most_downloaded_count,
        'last_download_date': last_download_date,
        'weekly_trends': weekly_trends,
        'weekly_total': weekly_total,
        'weekly_average': weekly_average,
        'max_weekly_count': max_weekly_count,
        'category_labels': category_labels,
        'category_data': category_data,
        'monthly_downloads': monthly_downloads,
        'favorite_category': favorite_category,
        'recommended_books': recommended_books,
    }
    
    return render(request, 'downloads/my_downloads.html', context)


from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BookDownload

@login_required
def remove_download(request, download_id):
    """Remove a download from user's history"""
    if request.method == 'POST':
        download = get_object_or_404(BookDownload, id=download_id, user=request.user)
        book_title = download.book.title
        download.delete()
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'"{book_title}" removed'})
        
        messages.success(request, f'"{book_title}" removed from your download history.')
        return redirect('downloads:my_downloads')
    
    return redirect('downloads:my_downloads')

@login_required
def clear_all_downloads(request):
    """Clear all download history for the user"""
    if request.method == 'POST':
        count = BookDownload.objects.filter(user=request.user).count()
        BookDownload.objects.filter(user=request.user).delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Cleared {count} records'})
        
        messages.success(request, f'Successfully cleared {count} download records.')
        return redirect('downloads:my_downloads')
    
    return redirect('downloads:my_downloads')
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse

import math

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
# from books.models import Book, BookReadOnline
@login_required
def clear_all_reading_history(request):
    """Clear all reading history for the user"""
    if request.method == 'POST':
        try:
            # Delete all reading history entries for the user
            deleted_count = BookReadOnline.objects.filter(user=request.user).delete()[0]
            
            return JsonResponse({
                'success': True, 
                'message': f'Successfully cleared {deleted_count} items from history',
                'deleted_count': deleted_count
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    # For GET requests, return a confirmation page or redirect
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
@login_required
def my_reading_history(request):
    """View user's reading history with statistics and achievements"""
    
    # Get all reading history for the user
    all_reads = BookReadOnline.objects.filter(
        user=request.user
    ).select_related('book').order_by('-last_activity')
    
    # Pagination (12 items per page)
    paginator = Paginator(all_reads, 12)
    page = request.GET.get('page', 1)
    
    try:
        reads = paginator.page(page)
    except PageNotAnInteger:
        reads = paginator.page(1)
    except EmptyPage:
        reads = paginator.page(paginator.num_pages)
    
    # Calculate statistics for all reads (not just current page)
    total_books = all_reads.count()
    
    # Total pages read
    total_pages_read = all_reads.aggregate(
        total=Sum('pages_read')
    )['total'] or 0
    
    # Total time spent in seconds
    total_time_seconds = all_reads.aggregate(
        total=Sum('time_spent')
    )['total'] or 0
    
    # Format total time spent
    if total_time_seconds >= 3600:
        hours = total_time_seconds // 3600
        minutes = (total_time_seconds % 3600) // 60
        total_time_spent = f"{hours}h {minutes}m"
    elif total_time_seconds >= 60:
        minutes = total_time_seconds // 60
        total_time_spent = f"{minutes} minutes"
    else:
        total_time_spent = f"{total_time_seconds} seconds"
    
    # Calculate reading streak
    reading_streak = calculate_reading_streak(all_reads)
    
    # Calculate achievements
    achievements = calculate_achievements(request.user, all_reads, total_books, total_pages_read)
    
    # Add calculated properties to each read object (using properties, not setting them)
    for read in reads:
        # These are properties that will be accessed in the template
        # DO NOT try to set them - they are read-only
        # Just access them directly in the template
        
        # Format time spent for display (store as attributes for template)
        if read.time_spent >= 3600:
            read.time_spent_hours = read.time_spent // 3600
            read.time_spent_minutes = (read.time_spent % 3600) // 60
        elif read.time_spent >= 60:
            read.time_spent_minutes = read.time_spent // 60
    
    context = {
        'reads': reads,
        'total_books': total_books,
        'total_pages_read': total_pages_read,
        'total_time_spent': total_time_spent,
        'reading_streak': reading_streak,
        'achievements': achievements,
    }
    
    return render(request, 'downloads/reading_history.html', context)

def calculate_reading_streak(reads):
    """Calculate the user's current reading streak in days"""
    if not reads:
        return 0
    
    # Get unique dates when user read books
    read_dates = set()
    for read in reads:
        if read.last_activity:
            read_dates.add(read.last_activity.date())
    
    if not read_dates:
        return 0
    
    # Sort dates in descending order
    sorted_dates = sorted(read_dates, reverse=True)
    today = timezone.now().date()
    
    streak = 0
    current_date = today
    
    # Check if user read today
    if today not in sorted_dates:
        # Check if user read yesterday to continue streak
        yesterday = today - timedelta(days=1)
        if yesterday not in sorted_dates:
            return 0
        current_date = yesterday
    
    # Calculate streak
    while current_date in sorted_dates:
        streak += 1
        current_date -= timedelta(days=1)
    
    return streak


def calculate_achievements(user, all_reads, total_books, total_pages_read):
    """Calculate user achievements based on reading activity"""
    achievements = []
    
    # First Book Achievement
    if total_books >= 1:
        achievements.append({
            'name': 'First Steps',
            'icon': 'fas fa-book',
            'description': 'Read your first book online'
        })
    
    # Bookworm Achievement
    if total_books >= 5:
        achievements.append({
            'name': 'Bookworm',
            'icon': 'fas fa-bookworm',
            'description': 'Read 5 books online'
        })
    
    # Avid Reader Achievement
    if total_books >= 10:
        achievements.append({
            'name': 'Avid Reader',
            'icon': 'fas fa-star',
            'description': 'Read 10 books online'
        })
    
    # Page Turner Achievement
    if total_pages_read >= 100:
        achievements.append({
            'name': 'Page Turner',
            'icon': 'fas fa-file-alt',
            'description': 'Read over 100 pages'
        })
    
    if total_pages_read >= 500:
        achievements.append({
            'name': 'Book Lover',
            'icon': 'fas fa-heart',
            'description': 'Read over 500 pages'
        })
    
    if total_pages_read >= 1000:
        achievements.append({
            'name': 'Master Reader',
            'icon': 'fas fa-crown',
            'description': 'Read over 1000 pages'
        })
    
    # Completionist Achievement
    completed_books = 0
    for read in all_reads:
        book_pages = read.book.pages or 0
        if book_pages > 0 and read.pages_read >= book_pages:
            completed_books += 1
    
    if completed_books >= 1:
        achievements.append({
            'name': 'Completionist',
            'icon': 'fas fa-check-circle',
            'description': 'Completed your first book'
        })
    
    if completed_books >= 5:
        achievements.append({
            'name': 'Master Completionist',
            'icon': 'fas fa-trophy',
            'description': 'Completed 5 books'
        })
    
    # Return top achievements (limit to 6)
    return achievements[:6]

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from books.models import Book
from .models import Purchase, BookDownload
import json
import logging

logger = logging.getLogger(__name__)


@login_required
def process_purchase(request, slug):
    """Process book purchase (for paid books)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
    
    try:
        # Parse JSON data
        data = json.loads(request.body) if request.body else {}
        book = get_object_or_404(Book, slug=slug, is_active=True)
        
        # Check if already purchased
        if Purchase.objects.filter(user=request.user, book=book, status='completed').exists():
            return JsonResponse({
                'success': True,
                'message': 'You already own this book',
                'download_url': reverse('downloads:download_book', args=[book.slug])
            })
        
        # For free books
        if book.is_free:
            purchase = Purchase.objects.create(
                user=request.user,
                book=book,
                amount=0,
                status='completed',
                payment_method=data.get('payment_method', 'free'),
                completed_at=timezone.now()
            )
            
            # Track download
            track_download(request, book)
            
            return JsonResponse({
                'success': True,
                'message': 'Book added to your library',
                'download_url': reverse('downloads:download_book', args=[book.slug])
            })
        
        # For paid books - create pending purchase
        purchase = Purchase.objects.create(
            user=request.user,
            book=book,
            amount=book.price,
            status='pending',
            payment_method=data.get('payment_method', 'mobile_money'),
            mobile_number=data.get('mobile_number', ''),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        # TODO: Integrate with actual payment gateway here
        # For demo purposes, we'll mark as completed immediately
        # In production, you would redirect to payment gateway and handle callbacks
        
        # Simulate successful payment (remove this in production)
        purchase.status = 'completed'
        purchase.completed_at = timezone.now()
        purchase.transaction_id = f"TXN_{int(timezone.now().timestamp())}_{request.user.id}"
        purchase.save()
        
        # Track download
        track_download(request, book)
        
        return JsonResponse({
            'success': True,
            'message': 'Purchase successful!',
            'download_url': reverse('downloads:download_book', args=[book.slug])
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error processing purchase: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def track_download(request, book):
    """Track book download in analytics"""
    try:
        BookDownload.objects.create(
            book=book,
            user=request.user if request.user.is_authenticated else None,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            is_premium=getattr(request.user, 'is_premium', False),
            amount_paid=0 if book.is_free else book.price,
            download_success=True
        )
        
        # Update book download count
        from django.db.models import F
        book.downloads_count = F('downloads_count') + 1
        book.save(update_fields=['downloads_count'])
    except Exception as e:
        logger.error(f"Error tracking download: {e}")


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def process_payment_callback(request):
    """Handle payment gateway callback (for paid books)"""
    if request.method == 'POST':
        # This is where you would handle payment gateway callbacks
        # Verify payment, update purchase status, etc.
        pass
    return JsonResponse({'status': 'ok'})


@login_required
def save_book(request, slug):
    """Save or unsave a book to user's library"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
    
    try:
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
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def is_book_saved(request, slug):
    """Check if a book is saved by the user"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    if not request.user.is_authenticated:
        return JsonResponse({'is_saved': False})
    
    try:
        book = get_object_or_404(Book, slug=slug, is_active=True)
        is_saved = SavedBook.objects.filter(user=request.user, book=book).exists()
        return JsonResponse({'is_saved': is_saved})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
def remove_reading_history(request, reading_id):
    """Remove a book from reading history"""
    if request.method == 'POST':
        try:
            reading_entry = get_object_or_404(
                BookReadOnline, 
                id=reading_id, 
                user=request.user
            )
            reading_entry.delete()
            return JsonResponse({'success': True, 'message': 'Removed from history'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


@login_required
def update_reading_progress(request, book_slug):
    """Update reading progress via AJAX"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            pages_read = data.get('pages_read', 0)
            time_spent = data.get('time_spent', 0)
            
            book = get_object_or_404(Book, slug=book_slug, is_active=True)
            
            # Get or create reading record
            reading_record, created = BookReadOnline.objects.get_or_create(
                user=request.user,
                book=book,
                defaults={
                    'pages_read': pages_read,
                    'time_spent': time_spent,
                    'last_activity': timezone.now(),
                    'total_pages': book.pages or 0,  # Store book.pages as total_pages
                    'completion_percentage': int((pages_read / (book.pages or 1)) * 100) if book.pages else 0
                }
            )
            
            if not created:
                # Update existing record
                if pages_read > reading_record.pages_read:
                    reading_record.pages_read = pages_read
                reading_record.time_spent += time_spent
                reading_record.last_activity = timezone.now()
                
                # Update completion percentage
                book_pages = book.pages or 0
                if book_pages > 0:
                    reading_record.completion_percentage = min(100, int((reading_record.pages_read / book_pages) * 100))
                
                reading_record.save()
            
            # Calculate progress percentage
            book_pages = book.pages or 0
            progress_percentage = min(100, int((reading_record.pages_read / book_pages) * 100)) if book_pages > 0 else 0
            
            return JsonResponse({
                'success': True,
                'pages_read': reading_record.pages_read,
                'time_spent': reading_record.time_spent,
                'progress_percentage': progress_percentage,
                'message': 'Progress updated'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def get_reading_statistics_api(request):
    """API endpoint to get reading statistics as JSON"""
    reads = BookReadOnline.objects.filter(user=request.user)
    
    # Daily reading statistics for the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_stats = {}
    
    for i in range(30):
        date = (timezone.now() - timedelta(days=i)).date()
        daily_stats[date.strftime('%Y-%m-%d')] = {
            'pages': 0,
            'time': 0,
            'books': 0
        }
    
    for read in reads:
        if read.last_activity and read.last_activity.date() >= thirty_days_ago.date():
            date_str = read.last_activity.date().strftime('%Y-%m-%d')
            if date_str in daily_stats:
                daily_stats[date_str]['pages'] += read.pages_read or 0
                daily_stats[date_str]['time'] += read.time_spent or 0
                daily_stats[date_str]['books'] += 1
    
    # Calculate average reading speed
    total_pages = reads.aggregate(total=Sum('pages_read'))['total'] or 0
    total_time = reads.aggregate(total=Sum('time_spent'))['total'] or 0
    avg_speed = (total_pages / (total_time / 60)) if total_time > 0 else 0  # pages per minute
    
    stats = {
        'total_books': reads.count(),
        'total_pages': total_pages,
        'total_time_minutes': round(total_time / 60, 1),
        'avg_speed_pages_per_minute': round(avg_speed, 1),
        'daily_stats': daily_stats,
        'reading_streak': calculate_reading_streak(reads),
    }
    
    return JsonResponse(stats)


@login_required
def update_reading_progress(request, book_slug):
    """Update reading progress via AJAX"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            pages_read = data.get('pages_read', 0)
            time_spent = data.get('time_spent', 0)
            
            book = get_object_or_404(Book, slug=book_slug, is_active=True)
            
            # Get or create reading record
            reading_record, created = BookReadOnline.objects.get_or_create(
                user=request.user,
                book=book,
                defaults={
                    'pages_read': pages_read,
                    'time_spent': time_spent,
                    'last_activity': timezone.now()
                }
            )
            
            if not created:
                # Update existing record
                if pages_read > reading_record.pages_read:
                    reading_record.pages_read = pages_read
                reading_record.time_spent += time_spent
                reading_record.last_activity = timezone.now()
                reading_record.save()
            
            # Calculate progress percentage
            total_pages = book.total_pages or 1
            progress_percentage = min(100, int((reading_record.pages_read / total_pages) * 100))
            
            return JsonResponse({
                'success': True,
                'pages_read': reading_record.pages_read,
                'time_spent': reading_record.time_spent,
                'progress_percentage': progress_percentage,
                'message': 'Progress updated'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# ==================== READING PROGRESS ====================

@require_http_methods(["POST"])
@login_required
def update_reading_progress(request):
    """AJAX endpoint to update reading progress"""
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        pages_read = data.get('pages_read', 0)
        time_spent = data.get('time_spent', 0)
        completed = data.get('completed', False)
        
        reading_session = BookReadOnline.objects.filter(
            book_id=book_id,
            user=request.user,
            completed=False
        ).last()
        
        if reading_session:
            reading_session.pages_read = pages_read
            reading_session.time_spent = time_spent
            reading_session.completed = completed
            reading_session.last_activity = timezone.now()
            
            # Update completion percentage
            if reading_session.total_pages > 0:
                reading_session.completion_percentage = int((pages_read / reading_session.total_pages) * 100)
            
            reading_session.save()
            return JsonResponse({'status': 'success'})
        
        return JsonResponse({'status': 'error', 'message': 'No active session found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ==================== UPLOAD BOOK ====================

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.files.uploadedfile import UploadedFile
from books.models import Book, Category, GradeLevel, Language

@staff_member_required
def upload_book(request):
    """Upload a new book (admin/staff only) with 3-level category hierarchy"""
    
    # Get data for dropdowns - make sure to get ALL active records
    categories = Category.objects.filter(is_active=True).order_by('order')
    grade_levels = GradeLevel.objects.filter(is_active=True).order_by('order')
    languages = Language.objects.filter(is_active=True).order_by('order')
    
    # Build category hierarchy information for the template
    # Categorize categories by their level
    top_level_categories = categories.filter(level=0, parent__isnull=True)
    subcategories = categories.filter(level=1)
    subjects = categories.filter(level=2)
    
    # Debug print to terminal
    print(f"Total Categories count: {categories.count()}")
    print(f"Top Level Categories (📁): {top_level_categories.count()}")
    print(f"Subcategories (📂): {subcategories.count()}")
    print(f"Subjects/Courses (📄): {subjects.count()}")
    print(f"Grade levels count: {grade_levels.count()}")
    print(f"Languages count: {languages.count()}")
    
    if request.method == 'POST':
        try:
            # Basic Information
            title = request.POST.get('title')
            author = request.POST.get('author')
            description = request.POST.get('description')
            
            # 3-Level Category Selection
            # The form uses three dropdowns, but only the final selected category (subject/course)
            # is submitted as 'category' since that's the actual category for the book
            category_id = request.POST.get('category')  # This is the final subject/course ID
            
            # Optional: You can also capture the intermediate selections for debugging/validation
            top_level_id = request.POST.get('top_level_category')
            sub_category_id = request.POST.get('sub_category')
            
            # Grade Level and Language
            grade_level_id = request.POST.get('grade_level')
            language_id = request.POST.get('language')
            
            # Pricing
            is_free = request.POST.get('is_free') == 'on'
            price = request.POST.get('price', 0)
            
            # Files
            pdf_file = request.FILES.get('pdf_file')
            cover_image = request.FILES.get('cover_image')
            
            # Additional Information
            publication_year = request.POST.get('publication_year')
            publisher = request.POST.get('publisher')
            pages = request.POST.get('pages', 0)
            isbn = request.POST.get('isbn')
            
            # Validation
            if not title:
                messages.error(request, 'Title is required')
                return render(request, 'downloads/upload_book.html', {
                    'categories': categories,
                    'grade_levels': grade_levels,
                    'languages': languages,
                    'top_level_categories': top_level_categories,
                    'subcategories': subcategories,
                    'subjects': subjects,
                })
            
            if not author:
                messages.error(request, 'Author is required')
                return render(request, 'downloads/upload_book.html', {
                    'categories': categories,
                    'grade_levels': grade_levels,
                    'languages': languages,
                    'top_level_categories': top_level_categories,
                    'subcategories': subcategories,
                    'subjects': subjects,
                })
            
            if not description:
                messages.error(request, 'Description is required')
                return render(request, 'downloads/upload_book.html', {
                    'categories': categories,
                    'grade_levels': grade_levels,
                    'languages': languages,
                    'top_level_categories': top_level_categories,
                    'subcategories': subcategories,
                    'subjects': subjects,
                })
            
            if not pdf_file:
                messages.error(request, 'PDF file is required')
                return render(request, 'downloads/upload_book.html', {
                    'categories': categories,
                    'grade_levels': grade_levels,
                    'languages': languages,
                    'top_level_categories': top_level_categories,
                    'subcategories': subcategories,
                    'subjects': subjects,
                })
            
            # Validate that a final category (subject/course) is selected
            if not category_id:
                messages.error(request, 'Please select a Subject/Course category (the final level of the hierarchy)')
                return render(request, 'downloads/upload_book.html', {
                    'categories': categories,
                    'grade_levels': grade_levels,
                    'languages': languages,
                    'top_level_categories': top_level_categories,
                    'subcategories': subcategories,
                    'subjects': subjects,
                })
            
            # Optional: Validate the selected category is indeed a level 2 category (subject)
            selected_category = Category.objects.filter(id=category_id, is_active=True).first()
            if selected_category and selected_category.level != 2:
                messages.warning(request, f'Note: Selected category "{selected_category.name}" is not a Subject/Course level. For best organization, please use Subject/Course level categories.')
                # Still allow it, but show warning
            
            # Validate file size for PDF (max 50MB)
            if pdf_file.size > 50 * 1024 * 1024:
                messages.error(request, 'PDF file must be less than 50MB')
                return render(request, 'downloads/upload_book.html', {
                    'categories': categories,
                    'grade_levels': grade_levels,
                    'languages': languages,
                    'top_level_categories': top_level_categories,
                    'subcategories': subcategories,
                    'subjects': subjects,
                })
            
            # Validate cover image size if provided (max 5MB)
            if cover_image and cover_image.size > 5 * 1024 * 1024:
                messages.error(request, 'Cover image must be less than 5MB')
                return render(request, 'downloads/upload_book.html', {
                    'categories': categories,
                    'grade_levels': grade_levels,
                    'languages': languages,
                    'top_level_categories': top_level_categories,
                    'subcategories': subcategories,
                    'subjects': subjects,
                })
            
            # Validate pages is a positive integer
            try:
                pages = int(pages) if pages else 0
                if pages < 0:
                    pages = 0
            except ValueError:
                pages = 0
            
            # Validate price
            try:
                price = float(price) if price else 0.00
                if price < 0:
                    price = 0.00
            except ValueError:
                price = 0.00
            
            # Create book
            book = Book.objects.create(
                title=title.strip(),
                author=author.strip(),
                description=description.strip(),
                category_id=category_id if category_id else None,
                grade_level_id=grade_level_id if grade_level_id else None,
                language_id=language_id if language_id else None,
                is_free=is_free,
                price=price if not is_free else 0,
                pdf_file=pdf_file,
                cover_image=cover_image,
                publication_year=publication_year if publication_year else None,
                publisher=publisher.strip() if publisher else '',
                pages=pages,
                isbn=isbn.strip() if isbn else '',
                is_active=True
            )
            
            # Log the successful upload with category hierarchy info
            category_path = []
            if book.category:
                cat = book.category
                category_path.append(cat.name)
                while cat.parent:
                    cat = cat.parent
                    category_path.insert(0, cat.name)
            
            print(f"Book uploaded successfully: {title}")
            print(f"Category path: {' → '.join(category_path) if category_path else 'None'}")
            
            messages.success(request, f'Book "{title}" uploaded successfully!')
            return redirect('books:book_detail', slug=book.slug)
            
        except Exception as e:
            messages.error(request, f'Error uploading book: {str(e)}')
            print(f"Upload error: {e}")
            import traceback
            traceback.print_exc()
    
    # GET request - show upload form
    context = {
        'categories': categories,
        'grade_levels': grade_levels,
        'languages': languages,
        'top_level_categories': top_level_categories,
        'subcategories': subcategories,
        'subjects': subjects,
    }
    return render(request, 'downloads/upload_book.html', context)

# ==================== DASHBOARD ====================
import csv
import zipfile
import io
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
from books.models import Book, Category, GradeLevel, Language

@staff_member_required
def download_bulk_template(request):
    """Download CSV template for bulk upload"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bulk_upload_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['title', 'author', 'description', 'category_id', 'grade_level_id', 
                     'language_id', 'is_free', 'price', 'publication_year', 'publisher', 
                     'pages', 'isbn'])
    writer.writerow(['Sample Book Title', 'Sample Author', 'Book description here', '1', '1', '1', 'True', '0', '2024', 'Sample Publisher', '100', '1234567890'])
    writer.writerow(['Another Book', 'Another Author', 'Another description', '2', '2', '1', 'False', '49.99', '2023', 'Another Publisher', '250', '0987654321'])
    
    return response


@staff_member_required
def bulk_upload(request):
    """Handle bulk upload of books via CSV/Excel"""
    if request.method != 'POST':
        return redirect('downloads:upload_book')
    
    data_file = request.FILES.get('data_file')
    zip_file = request.FILES.get('zip_file')
    
    if not data_file:
        messages.error(request, 'Please upload a data file')
        return redirect('downloads:upload_book')
    
    # Check file extension
    file_extension = data_file.name.split('.')[-1].lower()
    
    success_count = 0
    error_count = 0
    errors = []
    
    try:
        # Parse CSV file
        if file_extension == 'csv':
            # Read CSV file
            decoded_file = data_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            rows = list(csv_reader)
            
        elif file_extension in ['xls', 'xlsx']:
            messages.error(request, 'Excel files require pandas. Please use CSV format or install pandas: pip install pandas openpyxl')
            return redirect('downloads:upload_book')
        else:
            messages.error(request, 'Unsupported file format. Please upload CSV file.')
            return redirect('downloads:upload_book')
        
        # Process each row
        for index, row in enumerate(rows, start=2):  # Start from row 2 (1-indexed, row 1 is header)
            try:
                # Validate required fields
                title = row.get('title', '').strip()
                author = row.get('author', '').strip()
                description = row.get('description', '').strip()
                category_id = row.get('category_id', '').strip()
                
                if not title:
                    errors.append(f"Row {index}: Title is required")
                    error_count += 1
                    continue
                
                if not author:
                    errors.append(f"Row {index}: Author is required")
                    error_count += 1
                    continue
                
                if not description:
                    errors.append(f"Row {index}: Description is required")
                    error_count += 1
                    continue
                
                if not category_id:
                    errors.append(f"Row {index}: Category ID is required")
                    error_count += 1
                    continue
                
                # Parse values
                is_free = row.get('is_free', 'false').lower() in ['true', 'yes', '1']
                price = float(row.get('price', 0)) if row.get('price') else 0
                publication_year = int(row.get('publication_year')) if row.get('publication_year') and row.get('publication_year').isdigit() else None
                pages = int(row.get('pages', 0)) if row.get('pages') and row.get('pages').isdigit() else 0
                
                # Create book
                book = Book.objects.create(
                    title=title,
                    author=author,
                    description=description,
                    category_id=int(category_id),
                    grade_level_id=int(row.get('grade_level_id')) if row.get('grade_level_id') and row.get('grade_level_id').isdigit() else None,
                    language_id=int(row.get('language_id')) if row.get('language_id') and row.get('language_id').isdigit() else None,
                    is_free=is_free,
                    price=price,
                    publication_year=publication_year,
                    publisher=row.get('publisher', ''),
                    pages=pages,
                    isbn=row.get('isbn', ''),
                    is_active=True
                )
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {index}: {str(e)}")
        
        # Process ZIP file if provided
        if zip_file:
            # This would handle extracting PDFs and matching them to books
            # For now, just log that ZIP was uploaded
            messages.info(request, f'ZIP file "{zip_file.name}" received. PDFs need to be matched manually.')
        
        if success_count > 0:
            messages.success(request, f'Successfully uploaded {success_count} books!')
        if error_count > 0:
            messages.warning(request, f'{error_count} errors occurred. First few errors: {"; ".join(errors[:3])}')
        
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
    
    return redirect('downloads:upload_book')
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta
from .models import BookDownload, BookView, BookReadOnline, UserDownloadLimit
from books.models import Book, Category

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta
from .models import BookDownload, BookView, BookReadOnline, UserDownloadLimit
from books.models import Book, Category

@staff_member_required
def dashboard(request):
    """Downloads dashboard for staff users with enhanced analytics"""
    
    # Date ranges for trending data
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # ==================== STATISTICS ====================
    
    # Total counts
    total_downloads = BookDownload.objects.count()
    total_views = BookView.objects.count()
    total_reads = BookReadOnline.objects.count()
    active_users = UserDownloadLimit.objects.filter(downloads_today__gt=0).count()
    
    # Recent trends (last 30 days)
    recent_downloads_count = BookDownload.objects.filter(downloaded_at__date__gte=last_month).count()
    recent_views_count = BookView.objects.filter(viewed_at__date__gte=last_month).count()
    
    # Calculate percentage changes
    previous_downloads = BookDownload.objects.filter(
        downloaded_at__date__lt=last_month,
        downloaded_at__date__gte=last_month - timedelta(days=30)
    ).count()
    
    downloads_percentage = 0
    if previous_downloads > 0:
        downloads_percentage = round(((recent_downloads_count - previous_downloads) / previous_downloads) * 100, 1)
    
    # ==================== DOWNLOAD STATISTICS BY CATEGORY ====================
    category_stats = Category.objects.filter(
        is_active=True,
        books__is_active=True,
        books__downloads__isnull=False
    ).annotate(
        total_downloads=Sum('books__downloads_count')
    ).order_by('-total_downloads')[:5]
    
    # ==================== MONTHLY DOWNLOAD TRENDS (Last 12 Months) ====================
    monthly_labels = []
    monthly_downloads = []
    
    for i in range(11, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1, day=1)
        
        downloads_count = BookDownload.objects.filter(
            downloaded_at__gte=month_start,
            downloaded_at__lt=next_month
        ).count()
        
        monthly_labels.append(month_start.strftime('%b %Y'))
        monthly_downloads.append(downloads_count)
    
    # ==================== DAILY DOWNLOAD TRENDS (Last 7 Days) ====================
    daily_labels = []
    daily_downloads = []
    
    for i in range(6, -1, -1):
        day_date = today - timedelta(days=i)
        day_count = BookDownload.objects.filter(downloaded_at__date=day_date).count()
        daily_labels.append(day_date.strftime('%a'))
        daily_downloads.append(day_count)
    
    # ==================== DOWNLOADS BY CATEGORY FOR CHART ====================
    category_labels = []
    category_data = []
    category_colors = [
        '#059669', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', 
        '#10b981', '#6366f1', '#ec4899', '#14b8a6', '#f97316'
    ]
    
    categories = Category.objects.filter(is_active=True, books__is_active=True)
    for category in categories:
        downloads_count = BookDownload.objects.filter(
            book__category=category,
            book__is_active=True
        ).count()
        
        if downloads_count > 0:
            category_labels.append(category.name)
            category_data.append(downloads_count)
    
    if not category_data:
        category_labels = ['No Data']
        category_data = [1]
    
    # ==================== TOP USERS ====================
    top_users = UserDownloadLimit.objects.select_related('user').filter(
        downloads_total__gt=0
    ).order_by('-downloads_total')[:5]
    
    # ==================== POPULAR BOOKS ====================
    popular_books = Book.objects.filter(is_active=True).annotate(
        total_downloads=Sum('downloads_count'),
        total_views=Sum('views_count'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-total_downloads')[:5]
    
    # Add engagement rate to each book
    for book in popular_books:
        if book.total_views and book.total_views > 0:
            book.engagement = round((book.total_downloads / book.total_views) * 100, 1)
        else:
            book.engagement = 0
    
    # ==================== MOST VIEWED BOOKS ====================
    most_viewed_books = Book.objects.filter(is_active=True).annotate(
        total_views=Sum('views_count'),
        total_downloads=Sum('downloads_count')
    ).order_by('-total_views')[:5]
    
    for book in most_viewed_books:
        if book.total_views and book.total_views > 0:
            book.conversion = round((book.total_downloads / book.total_views) * 100, 1)
        else:
            book.conversion = 0
    
    # ==================== READING COMPLETION RATES ====================
    reading_sessions = BookReadOnline.objects.all()
    total_sessions = reading_sessions.count()
    completed_sessions = reading_sessions.filter(completed=True).count()
    avg_completion_percentage = reading_sessions.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0
    avg_time_spent = reading_sessions.aggregate(Avg('time_spent'))['time_spent__avg'] or 0
    
    completion_rate = 0
    if total_sessions > 0:
        completion_rate = round((completed_sessions / total_sessions) * 100, 1)
    
    # Format average time spent
    if avg_time_spent >= 3600:
        avg_time_formatted = f"{int(avg_time_spent // 3600)}h {int((avg_time_spent % 3600) // 60)}m"
    elif avg_time_spent >= 60:
        avg_time_formatted = f"{int(avg_time_spent // 60)}m {int(avg_time_spent % 60)}s"
    else:
        avg_time_formatted = f"{int(avg_time_spent)}s"
    
    # ==================== RECENT DOWNLOADS ====================
    recent_downloads = BookDownload.objects.select_related('book', 'user').order_by('-downloaded_at')[:15]
    
    # ==================== DEVICE STATISTICS ====================
    device_stats = {
        'mobile': 0,
        'desktop': 0,
        'tablet': 0,
        'unknown': 0
    }
    
    for download in BookDownload.objects.all()[:1000]:
        ua = download.user_agent.lower()
        if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
            device_stats['mobile'] += 1
        elif 'tablet' in ua or 'ipad' in ua:
            device_stats['tablet'] += 1
        elif 'windows' in ua or 'mac' in ua or 'linux' in ua:
            device_stats['desktop'] += 1
        else:
            device_stats['unknown'] += 1
    
    # ==================== PREMIUM VS FREE DOWNLOADS ====================
    premium_downloads = BookDownload.objects.filter(is_premium=True).count()
    free_downloads = total_downloads - premium_downloads
    premium_percentage = 0
    if total_downloads > 0:
        premium_percentage = round((premium_downloads / total_downloads) * 100, 1)
    
    # ==================== THIS MONTH VS LAST MONTH ====================
    this_month_downloads = BookDownload.objects.filter(
        downloaded_at__year=today.year,
        downloaded_at__month=today.month
    ).count()
    
    last_month_date = today.replace(day=1) - timedelta(days=1)
    last_month_downloads = BookDownload.objects.filter(
        downloaded_at__year=last_month_date.year,
        downloaded_at__month=last_month_date.month
    ).count()
    
    monthly_growth = 0
    if last_month_downloads > 0:
        monthly_growth = round(((this_month_downloads - last_month_downloads) / last_month_downloads) * 100, 1)
    
    context = {
        # Basic stats
        'total_downloads': total_downloads,
        'total_views': total_views,
        'total_reads': total_reads,
        'active_users': active_users,
        'recent_downloads_count': recent_downloads_count,
        'recent_views_count': recent_views_count,
        'downloads_percentage': downloads_percentage,
        
        # Category stats
        'category_stats': category_stats,
        
        # Chart data
        'monthly_labels': monthly_labels,
        'monthly_downloads': monthly_downloads,
        'daily_labels': daily_labels,
        'daily_downloads': daily_downloads,
        'category_labels': category_labels,
        'category_data': category_data,
        'category_colors': category_colors,
        
        # Top users
        'top_users': top_users,
        
        # Popular books
        'popular_books': popular_books,
        'most_viewed_books': most_viewed_books,
        
        # Reading stats
        'completion_rate': completion_rate,
        'avg_completion_percentage': round(avg_completion_percentage, 1),
        'avg_time_spent': avg_time_formatted,
        
        # Recent downloads
        'recent_downloads': recent_downloads,
        
        # Device stats
        'device_stats': device_stats,
        
        # Premium vs Free
        'premium_downloads': premium_downloads,
        'free_downloads': free_downloads,
        'premium_percentage': premium_percentage,
        
        # Monthly growth
        'this_month_downloads': this_month_downloads,
        'last_month_downloads': last_month_downloads,
        'monthly_growth': monthly_growth,
        
        # Date info
        'today': today,
        'last_week': last_week,
        'last_month': last_month,
    }
    
    return render(request, 'downloads/dashboard.html', context)
def track_view(request, slug):
    """Track book view via AJAX (simple version)"""
    try:
        book = get_object_or_404(Book, slug=slug, is_active=True)
        book.views_count += 1
        book.save(update_fields=['views_count'])
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

