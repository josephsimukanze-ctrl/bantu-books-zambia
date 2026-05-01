from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Sum
from .models import User, UserProfile, BiometricDevice, TwoFactorAuth
from downloads.models import BookDownload, UserDownloadLimit


class UserProfileInline(admin.StackedInline):
    """User profile inline in user admin"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fieldsets = (
        ('Personal Information', {
            'fields': ('bio', 'location', 'website', 'profile_picture')
        }),
        ('Social Links', {
            'fields': ('facebook', 'twitter', 'instagram', 'linkedin'),
            'classes': ('collapse',)
        }),
    )


class UserDownloadLimitInline(admin.StackedInline):
    """Download limit inline in user admin"""
    model = UserDownloadLimit
    can_delete = False
    verbose_name_plural = 'Download Limits'
    fieldsets = (
        ('Subscription', {
            'fields': ('subscription_tier', 'daily_limit', 'monthly_limit')
        }),
        ('Usage', {
            'fields': ('downloads_today', 'downloads_this_month', 'downloads_total'),
            'classes': ('collapse',)
        }),
        ('Reset Dates', {
            'fields': ('last_reset_date', 'last_monthly_reset'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('downloads_today', 'downloads_this_month', 'downloads_total', 
                       'last_reset_date', 'last_monthly_reset')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin for Bantu Books Zambia"""
    
    list_display = [
        'username', 'email', 'full_name', 'user_type_badge', 'phone_number',
        'downloads_today_count', 'total_downloads', 'is_active', 'date_joined'
    ]
    list_filter = [
        'user_type', 'is_active', 'is_staff', 'is_superuser', 
        'email_verified', 'date_joined'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    list_per_page = 25
    list_editable = ['is_active']
    
    fieldsets = (
        ('Login Information', {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        ('Account Type', {
            'fields': ('user_type', 'subscription_expiry'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('email_verified', 'two_factor_enabled', 'last_login_ip'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    inlines = [UserProfileInline, UserDownloadLimitInline]
    
    def full_name(self, obj):
        return obj.get_full_name() or '-'
    full_name.short_description = 'Full Name'
    
    def user_type_badge(self, obj):
        colors = {
            'basic': '#6b7280',
            'premium': '#f59e0b',
            'lifetime': '#10b981',
        }
        color = colors.get(obj.user_type, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_user_type_display().upper()
        )
    user_type_badge.short_description = 'Plan'
    
    def downloads_today_count(self, obj):
        """Show today's downloads"""
        try:
            limit = obj.download_limit
            return format_html(
                '<span style="font-weight: bold;">{}</span> / {}',
                limit.downloads_today,
                limit.daily_limit if limit.daily_limit else '∞'
            )
        except:
            return '0 / 20'
    downloads_today_count.short_description = 'Today'
    
    def total_downloads(self, obj):
        """Show total downloads"""
        try:
            limit = obj.download_limit
            return format_html('<span style="font-weight: bold;">{}</span>', limit.downloads_total)
        except:
            return '0'
    total_downloads.short_description = 'Total DL'
    
    actions = ['make_premium', 'make_basic', 'make_lifetime', 'activate_users', 'deactivate_users']
    
    def make_premium(self, request, queryset):
        updated = queryset.update(user_type='premium')
        # Also update download limits
        for user in queryset:
            limit, _ = UserDownloadLimit.objects.get_or_create(user=user)
            limit.subscription_tier = 'premium'
            limit.daily_limit = None
            limit.monthly_limit = None
            limit.save()
        self.message_user(request, f'{updated} users upgraded to Premium.')
    make_premium.short_description = 'Upgrade selected users to Premium'
    
    def make_basic(self, request, queryset):
        updated = queryset.update(user_type='basic')
        for user in queryset:
            limit, _ = UserDownloadLimit.objects.get_or_create(user=user)
            limit.subscription_tier = 'basic'
            limit.daily_limit = 20
            limit.monthly_limit = 500
            limit.save()
        self.message_user(request, f'{updated} users downgraded to Basic.')
    make_basic.short_description = 'Downgrade selected users to Basic'
    
    def make_lifetime(self, request, queryset):
        updated = queryset.update(user_type='lifetime', subscription_expiry=None)
        for user in queryset:
            limit, _ = UserDownloadLimit.objects.get_or_create(user=user)
            limit.subscription_tier = 'lifetime'
            limit.daily_limit = None
            limit.monthly_limit = None
            limit.save()
        self.message_user(request, f'{updated} users upgraded to Lifetime.')
    make_lifetime.short_description = 'Upgrade selected users to Lifetime'
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('download_limit')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User Profile Admin"""
    list_display = ['user', 'location', 'profile_picture_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'location']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Profile Information', {
            'fields': ('bio', 'location', 'website', 'profile_picture')
        }),
        ('Social Media', {
            'fields': ('facebook', 'twitter', 'instagram', 'linkedin'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />',
                obj.profile_picture.url
            )
        return format_html(
            '<div style="width: 40px; height: 40px; background: #f3f4f6; border-radius: 50%; display: flex; align-items: center; justify-content: center;">'
            '<i class="fas fa-user" style="color: #9ca3af;"></i></div>'
        )
    profile_picture_preview.short_description = 'Avatar'


@admin.register(BiometricDevice)
class BiometricDeviceAdmin(admin.ModelAdmin):
    """Biometric Device Admin"""
    list_display = ['user', 'device_name', 'is_active', 'last_used', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'device_name']
    readonly_fields = ['created_at', 'last_used']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Device Information', {
            'fields': ('device_name', 'credential_id', 'public_key')
        }),
        ('Status', {
            'fields': ('is_active', 'last_used')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    """2FA Admin"""
    list_display = ['user', 'is_enabled', 'backup_codes_count', 'created_at']
    list_filter = ['is_enabled', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['secret_key', 'created_at', 'updated_at']
    
    def backup_codes_count(self, obj):
        if obj.backup_codes:
            return len(obj.backup_codes)
        return 0
    backup_codes_count.short_description = 'Backup Codes'
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('2FA Settings', {
            'fields': ('is_enabled', 'secret_key', 'backup_codes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Custom Admin Site Headers
admin.site.site_header = 'Bantu Books Zambia - Admin Panel'
admin.site.site_title = 'Bantu Books Admin'
admin.site.index_title = 'Welcome to Bantu Books Admin Dashboard'

# Add custom admin views
admin.site.disable_action('delete_selected')


# Custom admin template filters
from django.contrib import messages

@admin.action(description='Reset download limits for selected users')
def reset_download_limits(modeladmin, request, queryset):
    for user in queryset:
        try:
            limit = user.download_limit
            limit.downloads_today = 0
            limit.downloads_this_month = 0
            limit.save()
        except:
            pass
    modeladmin.message_user(request, f'Download limits reset for {queryset.count()} users.')


# Add custom action
UserAdmin.actions.append(reset_download_limits)