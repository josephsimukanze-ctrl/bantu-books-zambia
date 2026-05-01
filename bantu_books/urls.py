from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Core app
    path('', include('core.urls')),
    
    # Authentication & User Management
    path('accounts/', include('accounts.urls')),
    
    # Books & Categories
    path('books/', include('books.urls')),
    
    # Downloads & Reading
    path('downloads/', include('downloads.urls')),
    
    # Payments (if you have a payments app)
    path('payments/', include('payments.urls')),
    
    # New: Dictionary App
    path('dictionary/', include('dictionary.urls')),
    
    # New: AI Assistant App
    path('ai-assistant/', include('ai_assistant.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers (optional)
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'