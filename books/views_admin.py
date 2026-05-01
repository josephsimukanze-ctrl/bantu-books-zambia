from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.urls import reverse
from .models import BookRequest, Book
from django.core.mail import send_mail
from django.conf import settings


@staff_member_required
def admin_approve_request(request, request_id):
    """Admin approve a book request"""
    book_request = get_object_or_404(BookRequest, id=request_id)
    book_request.status = 'approved'
    book_request.save()
    messages.success(request, f'Request for "{book_request.title}" has been approved.')
    return redirect('/admin/books/bookrequest/')


@staff_member_required
def admin_reject_request(request, request_id):
    """Admin reject a book request"""
    book_request = get_object_or_404(BookRequest, id=request_id)
    book_request.status = 'rejected'
    book_request.save()
    messages.success(request, f'Request for "{book_request.title}" has been rejected.')
    return redirect('/admin/books/bookrequest/')


@staff_member_required
def admin_add_book_to_request(request, request_id):
    """Admin add a book to fulfill a request"""
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
                    
                    Great news! The book you requested has been added to our library.
                    
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
            return redirect('/admin/books/bookrequest/')
    
    # GET request - show form to select book
    books = Book.objects.filter(is_active=True)
    context = {
        'book_request': book_request,
        'books': books,
    }
    return render(request, 'admin/books/bookrequest/add_book.html', context)