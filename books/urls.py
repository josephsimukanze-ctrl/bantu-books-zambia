from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    # ============ PUBLIC PATHS ============
    path('', views.book_list, name='book_list'),
    path('search/', views.search_books, name='search_books'),
    path('category/<slug:slug>/', views.category_books, name='category_books'),
    
    # ============ CONTRIBUTOR DASHBOARDS ============
    path('contributor-dashboard/', views.contributor_dashboard, name='contributor_dashboard'),
    path('earnings-dashboard/', views.earnings_dashboard, name='earnings_dashboard'),  # ADD THIS LINE
    path('sign-agreement/<int:application_id>/', views.sign_agreement, name='sign_agreement'),
    path('request-withdrawal/', views.request_withdrawal, name='request_withdrawal'),
    
    # ============ ADMIN/STAFF PATHS ============
    # Book Requests Management
    path('admin/manage-requests/', views.staff_manage_requests, name='staff_manage_requests'),
    path('admin/manage-applications/', views.manage_applications, name='manage_applications'),
    path('admin/manage-withdrawals/', views.manage_withdrawals, name='manage_withdrawals'),
    
    # User Management
    path('admin/users/', views.manage_users, name='manage_users'),
    path('admin/users/toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('admin/users/reset-limit/<int:user_id>/', views.reset_user_limit, name='reset_user_limit'),
    path('admin/users/reset-all-limits/', views.reset_all_limits, name='reset_all_limits'),
    path('admin/view-user/<int:user_id>/', views.view_user_profile, name='view_user_profile'),
    
    # Category Management
    path('admin/categories/', views.manage_categories, name='manage_categories'),
    path('admin/categories/add/', views.add_category, name='add_category'),
    path('admin/categories/<int:category_id>/', views.edit_category, name='edit_category'),
    path('admin/categories/update/<int:category_id>/', views.update_category, name='update_category'),
    path('admin/categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    
    # Grade Level Management
    path('admin/grades/', views.manage_grades, name='manage_grades'),
    path('admin/grades/add/', views.add_grade, name='add_grade'),
    path('admin/grades/<int:grade_id>/', views.edit_grade, name='edit_grade'),
    path('admin/grades/update/<int:grade_id>/', views.update_grade, name='update_grade'),
    path('admin/grades/delete/<int:grade_id>/', views.delete_grade, name='delete_grade'),
    
    # Language Management
    path('admin/languages/', views.manage_languages, name='manage_languages'),
    path('admin/languages/add/', views.add_language, name='add_language'),
    path('admin/languages/<int:language_id>/', views.edit_language, name='edit_language'),
    path('admin/languages/update/<int:language_id>/', views.update_language, name='update_language'),
    path('admin/languages/delete/<int:language_id>/', views.delete_language, name='delete_language'),
    
    # Downloads Management
    path('admin/downloads/', views.manage_downloads, name='manage_downloads'),
    path('admin/downloads/export/', views.export_downloads, name='export_downloads'),
    path('admin/downloads/counts/', views.get_download_counts, name='get_download_counts'),
    
    # Limits Management
    path('admin/limits/', views.manage_limits, name='manage_limits'),
    
    # ============ BOOK REQUEST PATHS (User) ============
    path('request-book/', views.request_book, name='request_book'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('received-books/', views.received_books, name='received_books'),
    
    # ============ CONTRIBUTOR PATHS ============
    path('apply-contributor/', views.apply_contributor, name='apply_contributor'),
    
    # ============ API PATHS (AJAX) ============
    path('api/application/<int:app_id>/', views.get_application_details, name='get_application_details'),
    path('api/approve-request/<int:request_id>/', views.api_approve_request, name='api_approve_request'),
    path('api/reject-request/<int:request_id>/', views.api_reject_request, name='api_reject_request'),
    path('api/admin/add-book-to-request/<int:request_id>/', views.admin_add_book_to_request, name='admin_add_book_to_request'),
    path('api/books/<slug:slug>/is-saved/', views.is_book_saved, name='is_book_saved'),
    path('api/books/<slug:slug>/save/', views.save_book, name='save_book_api'),
    
    # ============ BOOK DETAIL & REVIEWS (MUST BE LAST) ============
    path('track-view/<slug:slug>/', views.track_view, name='track_view'),
    path('<slug:slug>/add-review/', views.add_review, name='add_review'),
    path('<slug:slug>/', views.book_detail, name='book_detail'),  # MUST BE LAST
    path('api/category/<int:category_id>/', views.get_category_api, name='get_category_api'),
    path('<slug:slug>/add-review/', views.add_review, name='add_review'),
]