from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
import os


class Category(models.Model):
    """Hierarchical Category model for nested categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, default='book')
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='category_covers/', null=True, blank=True)
    # Hierarchical relationship - self-referential foreign key
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories',
        help_text="Parent category (leave empty for top-level categories)"
    )
    
    # Display settings
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Additional fields
    cover_image = models.ImageField(upload_to='category_covers/', null=True, blank=True)
    level = models.IntegerField(default=0, editable=False, help_text="Category depth level (0 = top level)")
    
    # Statistics (denormalized for performance)
    books_count = models.IntegerField(default=0, help_text="Cached count of books in this category")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['level', 'order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent', 'order']),
            models.Index(fields=['level', 'is_active']),
            models.Index(fields=['books_count']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Auto-calculate level based on parent
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('books:category_books', args=[self.slug])
    
    def get_book_count(self):
        """Get number of active books in this category"""
        return self.books.filter(is_active=True).count()
    
    def get_total_books_including_subcategories(self):
        """Get total books including all subcategories"""
        total = self.get_book_count()
        for subcat in self.subcategories.filter(is_active=True):
            total += subcat.get_total_books_including_subcategories()
        return total
    
    @property
    def icon_class(self):
        """Return FontAwesome icon class with prefix"""
        return f"fas fa-{self.icon}" if self.icon else "fas fa-folder"
    
    @property
    def breadcrumb(self):
        """Get breadcrumb trail"""
        crumbs = []
        current = self
        while current:
            crumbs.insert(0, {'name': current.name, 'slug': current.slug})
            current = current.parent
        return crumbs
    
    def get_full_path(self):
        """Get full path with all parents"""
        return ' > '.join([cat.name for cat in self.breadcrumb])
    
    def update_books_count(self):
        """Update the cached books count"""
        self.books_count = self.books.filter(is_active=True).count()
        self.save(update_fields=['books_count'])
    
    def get_descendants(self, include_self=False):
        """Get all descendant categories"""
        descendants = []
        if include_self:
            descendants.append(self)
        for child in self.subcategories.filter(is_active=True):
            descendants.extend(child.get_descendants(include_self=True))
        return descendants


class GradeLevel(models.Model):
    """Grade level model"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Grade Level"
        verbose_name_plural = "Grade Levels"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Language(models.Model):
    """Language model"""
    name = models.CharField(max_length=50, unique=True)
    native_name = models.CharField(max_length=50, blank=True)
    code = models.CharField(max_length=10, unique=True)
    icon = models.CharField(max_length=50, blank=True, default='language')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Language"
        verbose_name_plural = "Languages"
    
    def __str__(self):
        return self.name


class PriceRange(models.Model):
    """Price range for filtering"""
    name = models.CharField(max_length=50, unique=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_free = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Price Range"
        verbose_name_plural = "Price Ranges"
    
    def __str__(self):
        if self.is_free:
            return "Free Only"
        if self.min_price and self.max_price:
            return f"K{self.min_price} - K{self.max_price}"
        elif self.min_price:
            return f"K{self.min_price}+"
        elif self.max_price:
            return f"Under K{self.max_price}"
        return self.name


class Tag(models.Model):
    """Popular tags for books"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    usage_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class Book(models.Model):
    """Main Book model"""
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, blank=True, db_index=True)
    author = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    
    # Relationships
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='books',
        help_text="Select the category for this book (can be any level)"
    )
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    tags = models.ManyToManyField(Tag, related_name='books', blank=True)
    
    # Contributor relationship
    contributor = models.ForeignKey(
        'Contributor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        help_text="The contributor who uploaded this book"
    )
    
    # Pricing
    is_free = models.BooleanField(default=False, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    
    # Files
    pdf_file = models.FileField(upload_to='books/pdfs/%Y/%m/')
    epub_file = models.FileField(upload_to='books/epubs/%Y/%m/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='books/covers/%Y/%m/', null=True, blank=True)
    
    # Metadata
    publication_year = models.IntegerField(null=True, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    pages = models.IntegerField(default=0)
    isbn = models.CharField(max_length=13, blank=True)
    edition = models.CharField(max_length=50, blank=True)
    
    # File info
    file_size = models.IntegerField(default=0)
    file_format = models.CharField(max_length=10, default='PDF')
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    downloads_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    
    # Contributor earnings tracking
    earnings_paid = models.BooleanField(default=False, help_text="Whether contributor has been paid for this book")
    earnings_paid_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['grade_level', 'is_active']),
            models.Index(fields=['contributor']),
            models.Index(fields=['contributor', '-created_at']),
            models.Index(fields=['is_active', 'is_free']),
        ]
        verbose_name = "Book"
        verbose_name_plural = "Books"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.pdf_file and hasattr(self.pdf_file, 'size'):
            self.file_size = self.pdf_file.size
        
        # Set default price to 0 for free books
        if self.is_free:
            self.price = 0
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('books:book_detail', args=[self.slug])
    
    @property
    def formatted_price(self):
        if self.is_free:
            return "Free"
        return f"K{self.price:,.2f}"
    
    @property
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    @property
    def engagement_rate(self):
        """Calculate engagement rate (downloads/views)"""
        if self.views_count > 0:
            return round((self.downloads_count / self.views_count) * 100, 1)
        return 0
    
    def mark_earnings_paid(self):
        """Mark that contributor earnings have been paid"""
        self.earnings_paid = True
        self.earnings_paid_at = timezone.now()
        self.save(update_fields=['earnings_paid', 'earnings_paid_at'])
    
    @classmethod
    def get_contributor_books(cls, contributor_id):
        """Get all books by a specific contributor"""
        return cls.objects.filter(
            contributor_id=contributor_id,
            is_active=True
        ).order_by('-created_at')
    
    @classmethod
    def get_unpaid_contributor_earnings(cls):
        """Get all unpaid books for contributor payout"""
        return cls.objects.filter(
            contributor__isnull=False,
            earnings_paid=False,
            is_active=True
        ).select_related('contributor')
class BookReview(models.Model):
    """User reviews for books"""
    RATING_CHOICES = (
        (1, '⭐ 1 Star - Poor'),
        (2, '⭐⭐ 2 Stars - Fair'),
        (3, '⭐⭐⭐ 3 Stars - Good'),
        (4, '⭐⭐⭐⭐ 4 Stars - Very Good'),
        (5, '⭐⭐⭐⭐⭐ 5 Stars - Excellent'),
    )
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(max_length=1000)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['book', 'user']
        indexes = [
            models.Index(fields=['book', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_approved']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.rating} stars"
    
    @property
    def rating_stars(self):
        return '⭐' * self.rating + '☆' * (5 - self.rating)


class BookRequest(models.Model):
    """Book request model for users to request books"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    # Requestor Information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_requests')
    email = models.EmailField(help_text="Email to send notification")
    
    # Book Information
    title = models.CharField(max_length=200, help_text="Book title")
    author = models.CharField(max_length=200, blank=True, help_text="Author name (if known)")
    isbn = models.CharField(max_length=13, blank=True, help_text="ISBN number (if known)")
    
    # Additional Details
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='book_requests')
    description = models.TextField(blank=True, help_text="Additional description or reason for request")
    reason = models.TextField(blank=True, help_text="Why do you need this book? (e.g., studies, research)")
    assigned_book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True, related_name='fulfilled_requests')
    book_added_at = models.DateTimeField(null=True, blank=True)
    
    # Priority
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admin")
    
    # Notification
    notified_at = models.DateTimeField(null=True, blank=True)
    notified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='notified_requests')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Book Request"
        verbose_name_plural = "Book Requests"
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.title} requested by {self.user.username}"
    
    def get_status_badge(self):
        status_colors = {
            'pending': 'bg-yellow-100 text-yellow-800',
            'approved': 'bg-green-100 text-green-800',
            'processing': 'bg-blue-100 text-blue-800',
            'completed': 'bg-purple-100 text-purple-800',
            'rejected': 'bg-red-100 text-red-800',
        }
        return status_colors.get(self.status, 'bg-gray-100 text-gray-800')


class ContributorApplication(models.Model):
    """User application to become a book contributor/publisher"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('signed', 'Agreement Signed'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contributor_applications')
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    
    # Qualifications
    grade12_certificate = models.FileField(
        upload_to='contributor/certificates/%Y/%m/',
        validators=[FileExtensionValidator(['pdf', 'jpg', 'png'])],
        help_text="Upload your Grade 12 certificate"
    )
    nrc_document = models.FileField(
        upload_to='contributor/nrc/%Y/%m/',
        validators=[FileExtensionValidator(['pdf', 'jpg', 'png'])],
        help_text="Upload scanned NRC document"
    )
    
    # Experience
    teaching_experience = models.TextField(blank=True, help_text="Teaching experience if any")
    writing_experience = models.TextField(blank=True, help_text="Writing experience if any")
    subject_specialization = models.CharField(max_length=200, blank=True)
    
    # Additional Info
    reason_to_contribute = models.TextField(help_text="Why do you want to contribute books?")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Agreement
    agreement_signed = models.BooleanField(default=False)
    agreement_signed_at = models.DateTimeField(null=True, blank=True)
    agreement_signature = models.TextField(blank=True, help_text="Base64 encoded signature image")
    signature_ip = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contributor Application"
        verbose_name_plural = "Contributor Applications"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"


class ContributorAgreement(models.Model):
    """Agreement terms for contributors"""
    title = models.CharField(max_length=200, default="Contributor Agreement")
    content = models.TextField()
    version = models.CharField(max_length=20, default="1.0")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-version']
    
    def __str__(self):
        return f"Agreement v{self.version}"


class Contributor(models.Model):
    """Approved contributor with earnings tracking"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contributor_profile')
    application = models.OneToOneField(ContributorApplication, on_delete=models.CASCADE, related_name='contributor_profile')
    
    # Limits
    daily_upload_limit = models.IntegerField(default=10)
    today_uploads = models.IntegerField(default=0)
    last_upload_reset = models.DateField(auto_now_add=True)
    
    # Earnings
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    available_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_withdrawal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Payment settings
    payment_method = models.CharField(max_length=20, blank=True, choices=[
        ('airtel', 'Airtel Money'),
        ('mtn', 'MTN Mobile Money'),
        ('zamtel', 'Zamtel Kwacha'),
        ('bank', 'Bank Transfer'),
    ])
    payment_account = models.CharField(max_length=100, blank=True, help_text="Mobile number or bank account")
    
    # Status
    is_active = models.BooleanField(default=True)
    suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Contributor: {self.user.username}"
    
    def can_upload_today(self):
        """Check if contributor can upload more books today"""
        today = timezone.now().date()
        if self.last_upload_reset != today:
            self.today_uploads = 0
            self.last_upload_reset = today
            self.save(update_fields=['today_uploads', 'last_upload_reset'])
        return self.today_uploads < self.daily_upload_limit
    
    def increment_upload_count(self):
        """Increment today's upload count"""
        self.today_uploads += 1
        self.save(update_fields=['today_uploads'])
    
    def add_earnings(self, amount, book=None, description=""):
        """Add earnings from book upload"""
        self.total_earnings += amount
        self.available_balance += amount
        self.save(update_fields=['total_earnings', 'available_balance'])
        
        # Create earning record
        ContributorEarning.objects.create(
            contributor=self,
            book=book,
            amount=amount,
            description=description or f"Earnings from book upload"
        )
    
    def can_withdraw(self):
        """Check if user can withdraw (once per month, minimum K250)"""
        if self.available_balance < 250:
            return False, "Minimum withdrawal amount is K250"
        
        last_withdrawal = ContributorWithdrawal.objects.filter(
            contributor=self,
            status='completed'
        ).order_by('-created_at').first()
        
        if last_withdrawal:
            now = timezone.now()
            if last_withdrawal.created_at.month == now.month and last_withdrawal.created_at.year == now.year:
                return False, "You can only withdraw once per month"
        
        return True, "Eligible for withdrawal"
    
    def get_upload_limit_remaining(self):
        """Get remaining uploads for today"""
        if self.can_upload_today():
            return self.daily_upload_limit - self.today_uploads
        return 0


class ContributorEarning(models.Model):
    """Individual earning records"""
    contributor = models.ForeignKey(Contributor, on_delete=models.CASCADE, related_name='earnings')
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True, related_name='contributor_earnings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contributor', '-created_at']),
            models.Index(fields=['book']),
        ]
    
    def __str__(self):
        return f"{self.contributor.user.username} - K{self.amount}"


class ContributorWithdrawal(models.Model):
    """Withdrawal requests using payment system"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHODS = (
        ('airtel', 'Airtel Money'),
        ('mtn', 'MTN Mobile Money'),
        ('zamtel', 'Zamtel Kwacha'),
        ('bank', 'Bank Transfer'),
    )
    
    contributor = models.ForeignKey(Contributor, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(250)])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_details = models.CharField(max_length=200, help_text="Phone number or bank account details")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Payment transaction ID")
    admin_notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['contributor', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.contributor.user.username} - K{self.amount} - {self.get_status_display()}"