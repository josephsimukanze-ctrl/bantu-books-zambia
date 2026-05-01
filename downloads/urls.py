from django.urls import path
from . import views

app_name = 'downloads'

urlpatterns = [
    # Book Downloads
    path('download/<slug:slug>/', views.download_book, name='download_book'),
    path('my-downloads/', views.my_downloads, name='my_downloads'),
    path('remove-download/<int:download_id>/', views.remove_download, name='remove_download'),
    path('clear-all-downloads/', views.clear_all_downloads, name='clear_all_downloads'),
    
    # Read Online
    path('read/<slug:slug>/', views.read_online, name='read_online'),
    path('update-progress/', views.update_reading_progress, name='update_progress'),  # Keep this one
    path('reading-progress/<slug:book_slug>/', views.update_reading_progress, name='update_reading_progress'),
    
    # Reading History
    path('reading-history/', views.my_reading_history, name='reading_history'),
    path('reading-history/remove/<int:reading_id>/', views.remove_reading_history, name='remove_reading_history'),
    path('reading-history/clear-all/', views.clear_all_reading_history, name='clear_all_reading_history'),
    path('reading-history/stats/', views.get_reading_statistics_api, name='reading_stats_api'),
    
    # Purchases
    path('process-payment/<slug:slug>/', views.process_purchase, name='process_payment'),
    
    # Saved Books
    path('save/<slug:slug>/', views.save_book, name='save_book'),
    path('is-saved/<slug:slug>/', views.is_book_saved, name='is_book_saved'),
    path('admin-dashboard/', views.admin_analytics, name='admin_dashboard'), 
    # Upload & Dashboard
    path('upload/', views.upload_book, name='upload_book'),
    path('track-view/<slug:slug>/', views.track_view, name='track_view'),
    path('', views.dashboard, name='dashboard'),
    path('download-template/', views.download_bulk_template, name='download_bulk_template'),
path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
]