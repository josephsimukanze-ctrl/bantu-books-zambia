from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum, Count, Q, F
import os


class BookDownload(models.Model):
    """Track book downloads with detailed analytics"""
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='downloads')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='downloads', null=True, blank=True)
    ip_address = models.GenericIPAddressField(help_text="IP address of the downloader")
    user_agent = models.TextField(blank=True, help_text="Browser/Device information")
    is_premium = models.BooleanField(default=False, help_text="Whether the downloader has premium access")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Amount paid for this download")
    downloaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Enhanced tracking fields
    session_id = models.CharField(max_length=100, blank=True, db_index=True, help_text="User session identifier")
    referrer = models.URLField(blank=True, help_text="Referring page URL")
    download_duration = models.FloatField(default=0.0, help_text="Time taken to complete download in seconds")
    download_success = models.BooleanField(default=True, help_text="Whether download completed successfully")
    error_message = models.TextField(blank=True, help_text="Error message if download failed")
    
    class Meta:
        ordering = ['-downloaded_at']
        indexes = [
            models.Index(fields=['book', '-downloaded_at']),
            models.Index(fields=['user', '-downloaded_at']),
            models.Index(fields=['downloaded_at']),
            models.Index(fields=['book', 'user']),
            models.Index(fields=['session_id', '-downloaded_at']),
            models.Index(fields=['download_success']),
        ]
        verbose_name = "Book Download"
        verbose_name_plural = "Book Downloads"
    
    def __str__(self):
        return f"{self.book.title} downloaded by {self.user or 'Anonymous'} at {self.downloaded_at}"
    
    def save(self, *args, **kwargs):
        # Check if user is premium
        if self.user and hasattr(self.user, 'user_type'):
            self.is_premium = self.user.user_type in ['premium', 'lifetime']
        
        # Update book download count
        if not self.pk:  # New download
            from books.models import Book
            Book.objects.filter(id=self.book.id).update(downloads_count=F('downloads_count') + 1)
        
        super().save(*args, **kwargs)


class BookView(models.Model):
    """Track book views for analytics"""
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_views', null=True, blank=True)
    ip_address = models.GenericIPAddressField(help_text="IP address of the viewer")
    user_agent = models.TextField(blank=True, help_text="Browser/Device information")
    referrer = models.URLField(blank=True, help_text="Referring page URL")
    session_id = models.CharField(max_length=100, blank=True, db_index=True, help_text="User session identifier")
    view_duration = models.IntegerField(default=0, help_text="Time spent viewing in seconds")
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Additional fields
    device_type = models.CharField(max_length=20, blank=True, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('unknown', 'Unknown'),
    ], default='unknown')
    browser = models.CharField(max_length=50, blank=True, help_text="Browser name")
    os = models.CharField(max_length=50, blank=True, help_text="Operating system")
    is_unique_view = models.BooleanField(default=True, help_text="Whether this is a unique view")
    
    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['book', '-viewed_at']),
            models.Index(fields=['user', '-viewed_at']),
            models.Index(fields=['viewed_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['book', 'session_id']),
            models.Index(fields=['-viewed_at', 'is_unique_view']),
        ]
        verbose_name = "Book View"
        verbose_name_plural = "Book Views"
    
    def __str__(self):
        return f"{self.book.title} viewed by {self.user or 'Anonymous'} at {self.viewed_at}"
    
    def save(self, *args, **kwargs):
        # Update book view count for unique views only
        if not self.pk and self.is_unique_view:
            from books.models import Book
            Book.objects.filter(id=self.book.id).update(views_count=F('views_count') + 1)
        
        # Detect device type from user agent
        if self.user_agent:
            ua = self.user_agent.lower()
            if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
                self.device_type = 'mobile'
            elif 'tablet' in ua or 'ipad' in ua:
                self.device_type = 'tablet'
            else:
                self.device_type = 'desktop'
        
        super().save(*args, **kwargs)


class Purchase(models.Model):
    """Track book purchases"""
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHODS = (
        ('mobile_money', 'Mobile Money'),
        ('bank', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Payment gateway transaction ID")
    mobile_number = models.CharField(max_length=20, blank=True, help_text="Mobile money number")
    
    # Tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'book']
        ordering = ['-purchased_at']
        indexes = [
            models.Index(fields=['user', '-purchased_at']),
            models.Index(fields=['book', '-purchased_at']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_id']),
        ]
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.status}"
    
    def mark_completed(self):
        """Mark purchase as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_failed(self):
        """Mark purchase as failed"""
        self.status = 'failed'
        self.save(update_fields=['status'])


class SavedBook(models.Model):
    """Track books saved by users for later"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_books')
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'book']
        ordering = ['-saved_at']
        indexes = [
            models.Index(fields=['user', '-saved_at']),
            models.Index(fields=['book', '-saved_at']),
        ]
        verbose_name = "Saved Book"
        verbose_name_plural = "Saved Books"
    
    def __str__(self):
        return f"{self.user.username} saved {self.book.title}"


class BookReadOnline(models.Model):
    """Track online reading sessions with detailed metrics"""
    
    READING_MODES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
        ('sepia', 'Sepia Mode'),
    ]
    
    # Relationships
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='online_reads')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='online_reads', null=True, blank=True)
    
    # Reader identification
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the reader")
    user_agent = models.TextField(blank=True, help_text="Browser/Device information")
    session_id = models.CharField(max_length=100, blank=True, db_index=True, help_text="Anonymous session identifier")
    
    # Reading metrics
    pages_read = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Number of pages read")
    total_pages = models.IntegerField(default=0, help_text="Total pages in the book (synced from book.pages)")
    time_spent = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Time spent reading in seconds")
    completion_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Percentage of book completed")
    current_page = models.IntegerField(default=0, help_text="Last page the user was on")
    
    # Session tracking
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_activity = models.DateTimeField(auto_now=True, db_index=True)
    completed = models.BooleanField(default=False, help_text="Whether the reader completed the book")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When the book was completed")
    
    # Reading preferences
    font_size = models.IntegerField(default=100, validators=[MinValueValidator(50), MaxValueValidator(200)], help_text="Font size percentage")
    reading_mode = models.CharField(max_length=20, default='light', choices=READING_MODES)
    line_height = models.FloatField(default=1.5, help_text="Line height multiplier")
    
    # Session stats
    total_sessions = models.IntegerField(default=1, help_text="Number of sessions for this book")
    average_session_duration = models.IntegerField(default=0, help_text="Average session duration in seconds")
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['book', '-last_activity']),
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['completed']),
            models.Index(fields=['-last_activity']),
            models.Index(fields=['user', 'book']),
            models.Index(fields=['session_id', '-last_activity']),
        ]
        unique_together = ['user', 'book']  # One record per authenticated user per book
        verbose_name = "Online Reading Session"
        verbose_name_plural = "Online Reading Sessions"
    
    def __str__(self):
        reader = self.user.email if self.user else f'Anonymous ({self.session_id or self.ip_address})'
        return f"{self.book.title} read by {reader} - {self.completion_percentage}% complete"
    
    @property
    def remaining_pages(self):
        """Calculate remaining pages to read"""
        return max(0, (self.total_pages or self.book.pages or 0) - self.pages_read)
    
    @property
    def time_spent_formatted(self):
        """Format time spent as human-readable string"""
        if self.time_spent >= 3600:
            hours = self.time_spent // 3600
            minutes = (self.time_spent % 3600) // 60
            return f"{hours}h {minutes}m"
        elif self.time_spent >= 60:
            minutes = self.time_spent // 60
            return f"{minutes} minutes"
        else:
            return f"{self.time_spent} seconds"
    
    @property
    def time_spent_hours(self):
        return self.time_spent // 3600
    
    @property
    def time_spent_minutes(self):
        return (self.time_spent % 3600) // 60
    
    def update_progress(self, pages_read, time_spent, completed=False, current_page=None):
        """Update reading progress with validation"""
        total_pages = self.total_pages or self.book.pages or 0
        
        # Ensure progress doesn't go backwards
        if pages_read < self.pages_read:
            pages_read = self.pages_read
        
        self.pages_read = min(pages_read, total_pages) if total_pages > 0 else pages_read
        self.time_spent += time_spent
        self.last_activity = timezone.now()
        
        # Update current page if provided
        if current_page is not None:
            self.current_page = current_page
        
        # Update completion status
        if total_pages > 0 and self.pages_read >= total_pages:
            self.completed = True
            if not self.completed_at:
                self.completed_at = timezone.now()
        else:
            self.completed = completed
        
        # Update completion percentage
        self._update_completion_percentage()
        
        # Update average session duration
        if self.total_sessions > 0:
            self.average_session_duration = self.time_spent // self.total_sessions
        
        self.save()
    
    def _update_completion_percentage(self):
        """Update completion percentage based on pages read"""
        total_pages = self.total_pages or self.book.pages or 0
        if total_pages > 0:
            self.completion_percentage = min(100, int((self.pages_read / total_pages) * 100))
        else:
            self.completion_percentage = 0
    
    def save(self, *args, **kwargs):
        # Set total pages from book if not set
        if self.total_pages == 0 and self.book:
            self.total_pages = self.book.pages or 0
        
        # Update completion percentage
        self._update_completion_percentage()
        
        # Auto-mark as completed if pages read equals total pages
        total_pages = self.total_pages or self.book.pages or 0
        if total_pages > 0 and self.pages_read >= total_pages and not self.completed:
            self.completed = True
            self.completed_at = self.completed_at or timezone.now()
        
        # Validate pages_read doesn't exceed total_pages
        if total_pages > 0:
            self.pages_read = min(self.pages_read, total_pages)
        
        super().save(*args, **kwargs)


class UserDownloadLimit(models.Model):
    """Track user download limits and usage"""
    SUBSCRIPTION_TIERS = (
        ('basic', 'Basic - 20 downloads/day'),
        ('premium', 'Premium - Unlimited'),
        ('lifetime', 'Lifetime - Unlimited'),
        ('institution', 'Institution - 500 downloads/day'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='download_limit')
    subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_TIERS, default='basic')
    
    # Allow NULL for unlimited downloads
    daily_limit = models.IntegerField(null=True, blank=True, help_text="Maximum downloads per day (NULL = unlimited)")
    monthly_limit = models.IntegerField(null=True, blank=True, help_text="Maximum downloads per month (NULL = unlimited)")
    
    # Current usage
    downloads_today = models.IntegerField(default=0, help_text="Downloads count for today")
    downloads_this_month = models.IntegerField(default=0, help_text="Downloads count for this month")
    downloads_total = models.IntegerField(default=0, help_text="Total downloads all time")
    
    # Reset tracking
    last_reset_date = models.DateField(auto_now_add=True, help_text="Last date when daily count was reset")
    last_monthly_reset = models.DateField(auto_now_add=True, help_text="Last date when monthly count was reset")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Download Limit"
        verbose_name_plural = "User Download Limits"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['subscription_tier']),
        ]
    
    def __str__(self):
        daily_display = "Unlimited" if self.daily_limit is None else self.daily_limit
        return f"{self.user.username} - {self.downloads_today}/{daily_display} today"
    
    def get_limit_by_tier(self):
        """Get limits based on subscription tier"""
        limits = {
            'basic': {'daily': 20, 'monthly': 500},
            'premium': {'daily': None, 'monthly': None},
            'lifetime': {'daily': None, 'monthly': None},
            'institution': {'daily': None, 'monthly': None},
        }
        return limits.get(self.subscription_tier, limits['basic'])
    
    def save(self, *args, **kwargs):
        # Set limits based on subscription tier if not set
        if not self.pk:  # New object
            limits = self.get_limit_by_tier()
            if self.daily_limit is None:
                self.daily_limit = limits.get('daily')
            if self.monthly_limit is None:
                self.monthly_limit = limits.get('monthly')
        super().save(*args, **kwargs)
    
    def can_download(self):
        """Check if user can download"""
        # Premium and Lifetime have no limits
        if self.subscription_tier in ['premium', 'lifetime']:
            return True
        
        today = timezone.now().date()
        
        # Reset daily count if new day
        if self.last_reset_date != today:
            self.downloads_today = 0
            self.last_reset_date = today
            self.save(update_fields=['downloads_today', 'last_reset_date'])
        
        # Reset monthly count if new month
        current_month = today.replace(day=1)
        if self.last_monthly_reset != current_month:
            self.downloads_this_month = 0
            self.last_monthly_reset = current_month
            self.save(update_fields=['downloads_this_month', 'last_monthly_reset'])
        
        # Check daily limit
        if self.daily_limit is not None and self.downloads_today >= self.daily_limit:
            return False
        
        # Check monthly limit
        if self.monthly_limit is not None and self.downloads_this_month >= self.monthly_limit:
            return False
        
        return True
    
    def increment_download(self):
        """Increment download counts"""
        if not self.can_download():
            raise ValidationError("Download limit exceeded")
        
        self.downloads_today += 1
        self.downloads_this_month += 1
        self.downloads_total += 1
        self.save()
        return True
    
    def get_remaining_today(self):
        """Get remaining downloads for today"""
        if self.subscription_tier in ['premium', 'lifetime']:
            return "Unlimited"
        if self.daily_limit is None:
            return "Unlimited"
        return max(0, self.daily_limit - self.downloads_today)
    
    def get_remaining_monthly(self):
        """Get remaining downloads for the month"""
        if self.subscription_tier in ['premium', 'lifetime']:
            return "Unlimited"
        if self.monthly_limit is None:
            return "Unlimited"
        return max(0, self.monthly_limit - self.downloads_this_month)
    
    def reset_counts(self):
        """Reset daily and monthly counts"""
        self.downloads_today = 0
        self.downloads_this_month = 0
        self.last_reset_date = timezone.now().date()
        self.last_monthly_reset = timezone.now().date().replace(day=1)
        self.save()

class DownloadAnalytics(models.Model):
    """Aggregated download analytics for reporting"""
    date = models.DateField(unique=True, db_index=True)
    total_downloads = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    free_downloads = models.IntegerField(default=0)
    paid_downloads = models.IntegerField(default=0)
    premium_downloads = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    top_book = models.ForeignKey('books.Book', on_delete=models.SET_NULL, null=True, blank=True, related_name='top_analytics')
    
    # Additional fields
    average_download_time = models.FloatField(default=0.0, help_text="Average download time in seconds")
    failed_downloads = models.IntegerField(default=0, help_text="Number of failed downloads")
    unique_books_downloaded = models.IntegerField(default=0, help_text="Number of unique books downloaded")
    downloads_by_country = models.JSONField(default=dict, help_text="Downloads grouped by country")
    downloads_by_device = models.JSONField(default=dict, help_text="Downloads grouped by device type")
    
    class Meta:
        verbose_name = "Download Analytics"
        verbose_name_plural = "Download Analytics"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['-date', '-total_downloads']),
        ]
    
    def __str__(self):
        return f"Analytics for {self.date} - {self.total_downloads} downloads"
    
    @classmethod
    def generate_daily_report(cls, date=None):
        """Generate analytics report for a specific date"""
        if not date:
            date = timezone.now().date()
        
        downloads = BookDownload.objects.filter(
            downloaded_at__date=date,
            download_success=True
        )
        
        total_downloads = downloads.count()
        unique_users = downloads.values('user').distinct().count()
        
        report, created = cls.objects.get_or_create(date=date)
        report.total_downloads = total_downloads
        report.unique_users = unique_users
        report.free_downloads = downloads.filter(amount_paid=0).count()
        report.paid_downloads = downloads.filter(amount_paid__gt=0).count()
        report.premium_downloads = downloads.filter(is_premium=True).count()
        report.total_revenue = downloads.aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Get top book
        top_book_data = downloads.values('book').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        if top_book_data:
            report.top_book_id = top_book_data['book']
        
        report.save()
        return report
class Transaction(models.Model):
    """Payment transactions for user upgrades and purchases"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    PLAN_CHOICES = (
        ('monthly', 'Monthly Premium'),
        ('quarterly', 'Quarterly Premium'),
        ('yearly', 'Yearly Premium'),
        ('lifetime', 'Lifetime Access'),
        ('book_purchase', 'Book Purchase'),
    )
    
    PAYMENT_CHOICES = (
        ('airtel', 'Airtel Money'),
        ('mtn', 'MTN Mobile Money'),
        ('zamtel', 'Zamtel Kwacha'),
        ('bank', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
        ('auto', 'Auto Processed'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='download_transactions'
    )
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True, null=True)
    payment_details = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference_number = models.CharField(max_length=100, blank=True)
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user.email} - K{self.amount} - {self.status}"
    
    def get_status_display(self):
        """Get status display name"""
        status_dict = dict(self.STATUS_CHOICES)
        return status_dict.get(self.status, self.status)
    
    def get_plan_display(self):
        """Get plan display name"""
        plan_dict = dict(self.PLAN_CHOICES)
        return plan_dict.get(self.plan_type, self.plan_type if self.plan_type else 'N/A')
    
    def mark_completed(self):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.payment_confirmed_at = timezone.now()
        self.save(update_fields=['status', 'payment_confirmed_at'])
    
    def mark_failed(self):
        """Mark transaction as failed"""
        self.status = 'failed'
        self.save(update_fields=['status'])