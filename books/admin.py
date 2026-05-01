from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .models import (
    Category, GradeLevel, Language, PriceRange, Tag, Book, 
    BookReview, BookRequest, ContributorApplication, Contributor,
    ContributorEarning, ContributorWithdrawal
)


from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .models import (
    Category, GradeLevel, Language, PriceRange, Tag, Book, 
    BookReview, BookRequest, ContributorApplication, Contributor,
    ContributorEarning, ContributorWithdrawal
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Manage Categories with hierarchy"""
    list_display = ['name_indent', 'image_preview', 'slug', 'icon_preview', 'level', 'book_count', 'order', 'is_active']
    list_filter = ['is_active', 'parent', 'level']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'parent', 'icon', 'description')
        }),
        ('Image', {
            'fields': ('cover_image',),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('level',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['level']
    
    def name_indent(self, obj):
        """Display category name with indentation based on level"""
        indent = '&nbsp;&nbsp;&nbsp;' * obj.level
        if obj.level > 0:
            indent += '└─ '
        return format_html('{}{}', indent, obj.name)
    name_indent.short_description = 'Category Name'
    
    def image_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover;" />',
                obj.cover_image.url
            )
        return '-'
    image_preview.short_description = 'Image'
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<i class="fas fa-{}" style="color: #059669;"></i>', obj.icon)
        return '-'
    icon_preview.short_description = 'Icon'
    
    def book_count(self, obj):
        count = obj.books.filter(is_active=True).count()
        url = reverse('admin:books_book_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    book_count.short_description = 'Books'
    
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} categories marked as active.')
    make_active.short_description = 'Mark selected categories as active'
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} categories marked as inactive.')
    make_inactive.short_description = 'Mark selected categories as inactive'


# Remove any duplicate registration of Category below this line
# Make sure you don't have another @admin.register(Category) or admin.site.register(Category)

# ... rest of your admin registrations for other models ...

@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    """Manage Filter by Grade options"""
    list_display = ['name', 'slug', 'order', 'book_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']
    list_per_page = 20
    
    def book_count(self, obj):
        count = obj.books.filter(is_active=True).count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    book_count.short_description = 'Books'


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """Manage Filter by Language options"""
    list_display = ['name', 'native_name', 'code', 'order', 'book_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'native_name', 'code']
    list_editable = ['order', 'is_active']
    list_per_page = 20
    
    def book_count(self, obj):
        count = obj.books.filter(is_active=True).count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    book_count.short_description = 'Books'


@admin.register(PriceRange)
class PriceRangeAdmin(admin.ModelAdmin):
    """Manage Price Range filter options"""
    list_display = ['name', 'display_range', 'order', 'is_active']
    list_filter = ['is_active', 'is_free']
    list_editable = ['order', 'is_active']
    list_per_page = 20
    
    def display_range(self, obj):
        if obj.is_free:
            return 'Free Only'
        if obj.min_price and obj.max_price:
            return f'K{obj.min_price} - K{obj.max_price}'
        elif obj.min_price:
            return f'K{obj.min_price}+'
        elif obj.max_price:
            return f'Under K{obj.max_price}'
        return obj.name
    display_range.short_description = 'Range'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Manage Popular Tags"""
    list_display = ['name', 'slug', 'usage_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    list_per_page = 20


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Manage Books"""
    list_display = [
        'cover_preview', 'title', 'author', 'category_display', 
        'grade_display', 'language_display', 'price_display', 
        'downloads_count', 'is_active', 'is_featured'
    ]
    list_filter = ['category', 'grade_level', 'language', 'is_free', 'is_active', 'is_featured']
    search_fields = ['title', 'author', 'description', 'publisher']
    list_editable = ['is_active', 'is_featured']
    list_per_page = 25
    filter_horizontal = ['tags']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'description')
        }),
        ('Classification', {
            'fields': ('category', 'grade_level', 'language', 'tags')
        }),
        ('Pricing', {
            'fields': ('is_free', 'price')
        }),
        ('Files', {
            'fields': ('pdf_file', 'epub_file', 'cover_image')
        }),
        ('Metadata', {
            'fields': ('publication_year', 'publisher', 'pages', 'isbn', 'edition'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
    )
    
    readonly_fields = ['downloads_count', 'views_count', 'created_at', 'updated_at', 'file_size', 'file_format']
    
    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 40px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.cover_image.url
            )
        return format_html(
            '<div style="width: 40px; height: 50px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; border-radius: 4px;">'
            '<i class="fas fa-book" style="color: #9ca3af;"></i></div>'
        )
    cover_preview.short_description = 'Cover'
    
    def category_display(self, obj):
        return obj.category.name if obj.category else '-'
    category_display.short_description = 'Category'
    
    def grade_display(self, obj):
        return obj.grade_level.name if obj.grade_level else '-'
    grade_display.short_description = 'Grade'
    
    def language_display(self, obj):
        return obj.language.name if obj.language else '-'
    language_display.short_description = 'Language'
    
    def price_display(self, obj):
        if obj.is_free:
            # FIXED: format_html with a string that contains the content
            return format_html('{}', '<span style="color: #10b981; font-weight: bold;">FREE</span>')
        return format_html('<span style="color: #059669;">K{}</span>', obj.price)
    price_display.short_description = 'Price'
    
    actions = ['make_active', 'make_inactive', 'make_featured', 'make_unfeatured']
    
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} books marked as active.')
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} books marked as inactive.')
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} books marked as featured.')
    
    def make_unfeatured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} books removed from featured.')


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    """Manage Book Reviews"""
    list_display = ['book_title', 'user', 'rating_stars', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'created_at']
    search_fields = ['book__title', 'user__username', 'comment']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at']
    
    def book_title(self, obj):
        return obj.book.title
    book_title.short_description = 'Book'
    
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="font-size: 14px;">{} ({}/5)</span>', stars, obj.rating)
    rating_stars.short_description = 'Rating'


@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    """Manage Book Requests"""
    list_display = ['id', 'title', 'user_link', 'priority_badge', 'status_badge', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'author', 'user__username', 'user__email', 'isbn']
    list_per_page = 20
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'email', 'title', 'author', 'isbn', 'category')
        }),
        ('Request Details', {
            'fields': ('description', 'reason', 'priority')
        }),
        ('Status Management', {
            'fields': ('status', 'admin_notes')
        }),
        ('Book Assignment', {
            'fields': ('assigned_book', 'book_added_at'),
            'classes': ('collapse',)
        }),
        ('Notification', {
            'fields': ('notified_at', 'notified_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}" style="font-weight: bold;">{}</a><br><span style="color: #6b7280; font-size: 11px;">{}</span>', 
                          url, obj.user.username, obj.user.email)
    user_link.short_description = 'User'
    
    def priority_badge(self, obj):
        colors = {
            'urgent': '#ef4444',
            'high': '#f97316',
            'medium': '#eab308',
            'low': '#6b7280',
        }
        color = colors.get(obj.priority, '#6b7280')
        return format_html('<span style="background: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>', 
                          color, obj.get_priority_display().upper())
    priority_badge.short_description = 'Priority'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#eab308',
            'approved': '#3b82f6',
            'processing': '#8b5cf6',
            'completed': '#10b981',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html('<span style="background: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>', 
                          color, obj.get_status_display())
    status_badge.short_description = 'Status'
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} requests approved. You can now add books to them.')
    
    def reject_requests(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} requests rejected.')


@admin.register(ContributorApplication)
class ContributorApplicationAdmin(admin.ModelAdmin):
    """Manage Contributor Applications"""
    list_display = ['full_name', 'email', 'phone_number', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['full_name', 'email', 'phone_number', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': '#eab308',
            'approved': '#10b981',
            'rejected': '#ef4444',
            'signed': '#8b5cf6',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html('<span style="background: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>', 
                          color, obj.get_status_display())
    status_badge.short_description = 'Status'


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    """Manage Contributors"""
    list_display = ['user', 'total_earnings', 'available_balance', 'daily_upload_limit', 'is_active']
    list_filter = ['is_active', 'suspended']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['total_earnings', 'available_balance', 'pending_withdrawal', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Contributor Information', {
            'fields': ('user', 'application', 'is_active', 'suspended', 'suspension_reason')
        }),
        ('Upload Limits', {
            'fields': ('daily_upload_limit', 'today_uploads', 'last_upload_reset')
        }),
        ('Earnings', {
            'fields': ('total_earnings', 'available_balance', 'pending_withdrawal')
        }),
        ('Payment Settings', {
            'fields': ('payment_method', 'payment_account'),
            'classes': ('collapse',)
        }),
    )


# Custom admin site header
admin.site.site_header = 'Bantu Books Zambia - Admin Panel'
admin.site.site_title = 'Bantu Books Admin'
admin.site.index_title = 'Manage Your Digital Library'