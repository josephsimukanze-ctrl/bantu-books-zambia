from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    BookDownload, 
    BookView, 
    BookReadOnline, 
    UserDownloadLimit,
    DownloadAnalytics
)


@admin.register(BookDownload)
class BookDownloadAdmin(admin.ModelAdmin):
    """Admin for tracking book downloads"""
    list_display = [
        'book_title', 
        'user_info', 
        'ip_address', 
        'is_premium_badge', 
        'amount_paid', 
        'downloaded_at',
        'download_action'
    ]
    list_filter = [
        'is_premium', 
        'downloaded_at',
        ('user', admin.EmptyFieldListFilter),
    ]
    search_fields = [
        'book__title', 
        'book__author', 
        'user__username', 
        'user__email', 
        'ip_address'
    ]
    readonly_fields = [
        'book', 
        'user', 
        'ip_address', 
        'user_agent', 
        'is_premium', 
        'amount_paid', 
        'downloaded_at'
    ]
    date_hierarchy = 'downloaded_at'
    list_per_page = 25
    list_select_related = ['book', 'user']
    
    fieldsets = (
        ('Download Information', {
            'fields': ('book', 'user', 'ip_address', 'user_agent')
        }),
        ('Payment Information', {
            'fields': ('is_premium', 'amount_paid'),
            'classes': ('collapse',)
        }),
        ('Time Information', {
            'fields': ('downloaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def book_title(self, obj):
        """Display book title with link"""
        url = reverse('admin:books_book_change', args=[obj.book.id])
        return format_html(
            '<a href="{}" style="font-weight: bold; color: #059669;">{}</a>',
            url, obj.book.title
        )
    book_title.short_description = 'Book'
    book_title.admin_order_field = 'book__title'
    
    def user_info(self, obj):
        """Display user information"""
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.id])
            return format_html(
                '<a href="{}">{}</a><br><span style="color: #6b7280; font-size: 11px;">{}</span>',
                url, obj.user.username, obj.user.email
            )
        return format_html(
            '<span style="color: #9ca3af;">Anonymous User</span>'
        )
    user_info.short_description = 'User'
    
    def is_premium_badge(self, obj):
        """Display premium status badge"""
        if obj.is_premium:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Premium</span>'
            )
        return format_html(
            '<span style="background: #6b7280; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Basic</span>'
        )
    is_premium_badge.short_description = 'Type'
    
    def download_action(self, obj):
        """Action buttons"""
        if obj.book.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" style="background: #059669; color: white; padding: 4px 12px; border-radius: 6px; text-decoration: none; font-size: 12px;">'
                '<i class="fas fa-download"></i> View File</a>',
                obj.book.pdf_file.url
            )
        return '-'
    download_action.short_description = 'Action'
    
    def has_add_permission(self, request):
        """Disable manual addition of downloads"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of downloads"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for admins"""
        return request.user.is_superuser
    
    actions = ['delete_selected']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('book', 'user')


@admin.register(BookView)
class BookViewAdmin(admin.ModelAdmin):
    """Admin for tracking book views"""
    list_display = [
        'book_title', 
        'user_info', 
        'ip_address', 
        'view_duration_display', 
        'viewed_at'
    ]
    list_filter = ['viewed_at']
    search_fields = ['book__title', 'user__username', 'ip_address']
    readonly_fields = ['book', 'user', 'ip_address', 'user_agent', 'referrer', 'session_id', 'view_duration', 'viewed_at']
    date_hierarchy = 'viewed_at'
    list_per_page = 25
    
    def book_title(self, obj):
        url = reverse('admin:books_book_change', args=[obj.book.id])
        return format_html('<a href="{}">{}</a>', url, obj.book.title)
    book_title.short_description = 'Book'
    
    def user_info(self, obj):
        if obj.user:
            return obj.user.username
        return 'Anonymous'
    user_info.short_description = 'User'
    
    def view_duration_display(self, obj):
        if obj.view_duration >= 60:
            minutes = obj.view_duration // 60
            seconds = obj.view_duration % 60
            return f"{minutes}m {seconds}s"
        return f"{obj.view_duration}s"
    view_duration_display.short_description = 'Duration'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BookReadOnline)
class BookReadOnlineAdmin(admin.ModelAdmin):
    """Admin for tracking online reading sessions"""
    list_display = [
        'book_title',
        'user_info',
        'completion_display',
        'pages_read_display',
        'time_spent_display',
        'last_activity',
        'is_completed'
    ]
    list_filter = ['completed', 'last_activity']
    search_fields = ['book__title', 'user__username', 'ip_address']
    readonly_fields = [
        'book', 'user', 'ip_address', 'user_agent', 
        'pages_read', 'total_pages', 'time_spent', 
        'completion_percentage', 'started_at', 'last_activity', 
        'completed', 'font_size', 'reading_mode'
    ]
    list_per_page = 25
    date_hierarchy = 'last_activity'
    
    fieldsets = (
        ('Reading Session', {
            'fields': ('book', 'user', 'ip_address')
        }),
        ('Progress', {
            'fields': ('pages_read', 'total_pages', 'completion_percentage', 'time_spent')
        }),
        ('Status', {
            'fields': ('completed', 'started_at', 'last_activity')
        }),
        ('Preferences', {
            'fields': ('font_size', 'reading_mode'),
            'classes': ('collapse',)
        }),
    )
    
    def book_title(self, obj):
        url = reverse('admin:books_book_change', args=[obj.book.id])
        return format_html('<a href="{}">{}</a>', url, obj.book.title)
    book_title.short_description = 'Book'
    
    def user_info(self, obj):
        if obj.user:
            return obj.user.username
        return 'Anonymous'
    user_info.short_description = 'User'
    
    def completion_display(self, obj):
        color = '#10b981' if obj.completion_percentage >= 80 else '#f59e0b' if obj.completion_percentage >= 50 else '#ef4444'
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<div style="flex: 1; height: 6px; background: #e5e7eb; border-radius: 3px; overflow: hidden; width: 80px;">'
            '<div style="width: {}%; height: 100%; background: {}; border-radius: 3px;"></div>'
            '</div>'
            '<span style="font-weight: bold;">{}%</span></div>',
            obj.completion_percentage, color, obj.completion_percentage
        )
    completion_display.short_description = 'Progress'
    
    def pages_read_display(self, obj):
        return f"{obj.pages_read} / {obj.total_pages}"
    pages_read_display.short_description = 'Pages Read'
    
    def time_spent_display(self, obj):
        if obj.time_spent >= 3600:
            hours = obj.time_spent // 3600
            minutes = (obj.time_spent % 3600) // 60
            return f"{hours}h {minutes}m"
        elif obj.time_spent >= 60:
            minutes = obj.time_spent // 60
            return f"{minutes}m"
        return f"{obj.time_spent}s"
    time_spent_display.short_description = 'Time Spent'
    
    def is_completed(self, obj):
        if obj.completed:
            return format_html('<span style="color: #10b981;">✓ Completed</span>')
        return format_html('<span style="color: #f59e0b;">● In Progress</span>')
    is_completed.short_description = 'Status'


@admin.register(UserDownloadLimit)
class UserDownloadLimitAdmin(admin.ModelAdmin):
    """Admin for managing user download limits"""
    list_display = [
        'user_link',
        'subscription_tier',
        'daily_usage',
        'monthly_usage',
        'downloads_total_display',
        'can_download_badge',
        'last_reset'
    ]
    list_filter = ['subscription_tier', 'last_reset_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['downloads_total', 'created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'subscription_tier')
        }),
        ('Limits', {
            'fields': ('daily_limit', 'monthly_limit')
        }),
        ('Usage', {
            'fields': ('downloads_today', 'downloads_this_month', 'downloads_total')
        }),
        ('Reset Information', {
            'fields': ('last_reset_date', 'last_monthly_reset'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def daily_usage(self, obj):
        if obj.daily_limit:
            percentage = (obj.downloads_today / obj.daily_limit) * 100
            color = '#10b981' if percentage < 80 else '#f59e0b' if percentage < 100 else '#ef4444'
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<div style="flex: 1; height: 6px; background: #e5e7eb; border-radius: 3px; overflow: hidden; width: 80px;">'
                '<div style="width: {}%; height: 100%; background: {}; border-radius: 3px;"></div>'
                '</div>'
                '<span>{}/{}</span></div>',
                min(percentage, 100), color, obj.downloads_today, obj.daily_limit
            )
        return "Unlimited"
    daily_usage.short_description = 'Daily Usage'
    
    def monthly_usage(self, obj):
        if obj.monthly_limit:
            percentage = (obj.downloads_this_month / obj.monthly_limit) * 100
            return f"{obj.downloads_this_month} / {obj.monthly_limit} ({percentage:.1f}%)"
        return "Unlimited"
    monthly_usage.short_description = 'Monthly Usage'
    
    def downloads_total_display(self, obj):
        """Display total downloads"""
        return obj.downloads_total
    downloads_total_display.short_description = 'Total Downloads'
    downloads_total_display.admin_order_field = 'downloads_total'
    
    def can_download_badge(self, obj):
        if obj.can_download():
            return format_html('<span style="color: #10b981;">✓ Can Download</span>')
        return format_html('<span style="color: #ef4444;">✗ Limit Reached</span>')
    can_download_badge.short_description = 'Status'
    
    def last_reset(self, obj):
        return obj.last_reset_date
    last_reset.short_description = 'Last Reset'
    
    actions = ['reset_daily_counts', 'reset_monthly_counts']
    
    def reset_daily_counts(self, request, queryset):
        for obj in queryset:
            obj.downloads_today = 0
            obj.last_reset_date = timezone.now().date()
            obj.save()
        self.message_user(request, f'{queryset.count()} user(s) daily counts reset.')
    reset_daily_counts.short_description = 'Reset daily download counts'
    
    def reset_monthly_counts(self, request, queryset):
        for obj in queryset:
            obj.downloads_this_month = 0
            obj.last_monthly_reset = timezone.now().date().replace(day=1)
            obj.save()
        self.message_user(request, f'{queryset.count()} user(s) monthly counts reset.')
    reset_monthly_counts.short_description = 'Reset monthly download counts'


@admin.register(DownloadAnalytics)
class DownloadAnalyticsAdmin(admin.ModelAdmin):
    """Admin for viewing download analytics"""
    list_display = [
        'date',
        'total_downloads',
        'unique_users',
        'free_vs_paid',
        'premium_downloads',
        'total_revenue',
        'top_book_title'
    ]
    list_filter = ['date']
    search_fields = ['top_book__title']
    readonly_fields = [
        'date', 'total_downloads', 'unique_users', 'free_downloads',
        'paid_downloads', 'premium_downloads', 'total_revenue', 'top_book'
    ]
    date_hierarchy = 'date'
    list_per_page = 30
    
    def free_vs_paid(self, obj):
        total = obj.free_downloads + obj.paid_downloads
        if total > 0:
            free_percent = (obj.free_downloads / total) * 100
            paid_percent = (obj.paid_downloads / total) * 100
            return format_html(
                '<div style="display: flex; height: 20px; border-radius: 10px; overflow: hidden;">'
                '<div style="width: {}%; background: #10b981; text-align: center; color: white; font-size: 10px;">Free</div>'
                '<div style="width: {}%; background: #f59e0b; text-align: center; color: white; font-size: 10px;">Paid</div>'
                '</div>',
                free_percent, paid_percent
            )
        return '-'
    free_vs_paid.short_description = 'Free vs Paid'
    
    def top_book_title(self, obj):
        if obj.top_book:
            url = reverse('admin:books_book_change', args=[obj.top_book.id])
            return format_html('<a href="{}">{}</a>', url, obj.top_book.title)
        return '-'
    top_book_title.short_description = 'Top Book'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser