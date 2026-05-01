from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.conf import settings
import uuid


class User(AbstractUser):
    """
    Custom User model for Bantu Books Zambia
    """
    USER_TYPE_CHOICES = (
        ('guest', 'Guest Account'),
        ('basic', 'Basic - Free Plan'),
        ('premium', 'Premium - Monthly Subscription'),
        ('lifetime', 'Lifetime - One-time Payment'),
        ('institution', 'Institutional License'),
    )
    
    PROVINCE_CHOICES = (
        ('central', 'Central Province'),
        ('copperbelt', 'Copperbelt Province'),
        ('eastern', 'Eastern Province'),
        ('luapula', 'Luapula Province'),
        ('lusaka', 'Lusaka Province'),
        ('muchinga', 'Muchinga Province'),
        ('northern', 'Northern Province'),
        ('northwestern', 'North-Western Province'),
        ('southern', 'Southern Province'),
        ('western', 'Western Province'),
    )
    
    # Phone number validation for Zambia (+260...)
    phone_regex = RegexValidator(
        regex=r'^\+?260?\d{9}$',
        message="Phone number must be in format: +260XXXXXXXXX or 09XXXXXXXX"
    )
    
    # User type and basic info
    user_type = models.CharField(
        max_length=20, 
        choices=USER_TYPE_CHOICES, 
        default='basic'
    )
    phone_number = models.CharField(
        max_length=15, 
        validators=[phone_regex],
        unique=True, 
        null=True, 
        blank=True
    )
    national_id = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        help_text="Zambian National Registration Card (NRC) number"
    )
    province = models.CharField(
        max_length=50, 
        choices=PROVINCE_CHOICES, 
        null=True, 
        blank=True
    )
    district = models.CharField(max_length=100, blank=True)
    constituency = models.CharField(max_length=100, blank=True)
    school_or_work = models.CharField(max_length=200, blank=True)
    
    # Subscription and credits
    subscription_expiry = models.DateTimeField(null=True, blank=True)
    credits_balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Balance in Zambian Kwacha (K)"
    )
    
    # Profile
    profile_picture = models.ImageField(
        upload_to='profile_pics/%Y/%m/', 
        null=True, 
        blank=True
    )
    bio = models.TextField(max_length=500, blank=True)
    
    # Security
    email_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    verification_token = models.CharField(max_length=100, blank=True)
    reset_token = models.CharField(max_length=100, blank=True)
    
    # Statistics
    total_downloads = models.IntegerField(default=0)
    total_uploads = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['national_id']),
            models.Index(fields=['-date_joined']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_premium_active(self):
        """Check if user has active premium subscription"""
        if self.user_type == 'lifetime':
            return True
        if self.user_type == 'premium' and self.subscription_expiry:
            return self.subscription_expiry > timezone.now()
        return False
    
    def get_daily_download_limit(self):
        """Get daily download limit based on user type"""
        limits = {
            'guest': 5,
            'basic': 20,
            'premium': None,  # Unlimited
            'lifetime': None,  # Unlimited
            'institution': 500
        }
        return limits.get(self.user_type, 5)
    
    def get_remaining_daily_downloads(self):
        """Calculate remaining downloads for today"""
        from downloads.models import BookDownload
        limit = self.get_daily_download_limit()
        if limit is None:
            return None  # Unlimited
        
        today = timezone.now().date()
        downloads_today = BookDownload.objects.filter(
            user=self,
            downloaded_at__date=today
        ).count()
        
        return max(0, limit - downloads_today)
    
    def can_download(self):
        """Check if user can download more today"""
        remaining = self.get_remaining_daily_downloads()
        if remaining is None:
            return True
        return remaining > 0
    
    def add_credits(self, amount):
        """Add credits to user account"""
        from decimal import Decimal
        self.credits_balance += Decimal(str(amount))
        self.save(update_fields=['credits_balance'])
    
    def deduct_credits(self, amount):
        """Deduct credits from user account"""
        from decimal import Decimal
        if self.credits_balance >= Decimal(str(amount)):
            self.credits_balance -= Decimal(str(amount))
            self.save(update_fields=['credits_balance'])
            return True
        return False
    
    def upgrade_to_premium(self, months=1):
        """Upgrade user to premium subscription"""
        from datetime import timedelta
        self.user_type = 'premium'
        if self.subscription_expiry and self.subscription_expiry > timezone.now():
            self.subscription_expiry += timedelta(days=30 * months)
        else:
            self.subscription_expiry = timezone.now() + timedelta(days=30 * months)
        self.save(update_fields=['user_type', 'subscription_expiry'])
    
    def get_download_limit_object(self):
        """Get or create download limit object"""
        from downloads.models import UserDownloadLimit
        limit, created = UserDownloadLimit.objects.get_or_create(user=self)
        return limit


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Personal Bio
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    # Profile Image
    profile_picture = models.ImageField(upload_to='profile_pics/%Y/%m/', null=True, blank=True)
    
    # Social Media Links
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    newsletter_subscribed = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_avatar_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return f"https://ui-avatars.com/api/?name={self.user.username}&background=059669&color=fff&size=150"


class BiometricDevice(models.Model):
    """Store biometric authentication devices for users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='biometric_devices')
    device_name = models.CharField(max_length=100, help_text="Device name (e.g., iPhone 12, Laptop)")
    credential_id = models.CharField(max_length=255, unique=True, help_text="WebAuthn credential ID")
    public_key = models.TextField(help_text="WebAuthn public key")
    
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Biometric Device"
        verbose_name_plural = "Biometric Devices"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['credential_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_name}"
    
    def mark_used(self):
        """Update last used timestamp"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])


class TwoFactorAuth(models.Model):
    """Store 2FA settings for users"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='two_factor_auth')
    
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=100, blank=True, help_text="TOTP secret key")
    backup_codes = models.JSONField(default=list, blank=True, help_text="List of backup codes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Two Factor Authentication"
        verbose_name_plural = "Two Factor Authentications"
    
    def __str__(self):
        return f"{self.user.username} - {'Enabled' if self.is_enabled else 'Disabled'}"
    
    def generate_backup_codes(self, count=10):
        """Generate new backup codes"""
        import secrets
        codes = [secrets.token_hex(5) for _ in range(count)]
        self.backup_codes = codes
        self.save(update_fields=['backup_codes'])
        return codes
    
    def verify_backup_code(self, code):
        """Verify and consume a backup code"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save(update_fields=['backup_codes'])
            return True
        return False
    
    def enable_2fa(self, secret_key):
        """Enable 2FA for user"""
        self.is_enabled = True
        self.secret_key = secret_key
        self.save(update_fields=['is_enabled', 'secret_key'])
    
    def disable_2fa(self):
        """Disable 2FA for user"""
        self.is_enabled = False
        self.secret_key = ''
        self.backup_codes = []
        self.save(update_fields=['is_enabled', 'secret_key', 'backup_codes'])


class LoginHistory(models.Model):
    """Track user login history"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='login_history')
    
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, blank=True, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('unknown', 'Unknown'),
    ])
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    login_success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=100, blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Login History"
        verbose_name_plural = "Login History"
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['login_success']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M')} - {'Success' if self.login_success else 'Failed'}"


from django.db import models
from django.conf import settings
from django.utils import timezone
import base64
import json

class BiometricCredential(models.Model):
    """Store biometric credentials for WebAuthn"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='biometric_credentials'
    )
    credential_id = models.CharField(
        max_length=255, 
        unique=True, 
        db_index=True,
        help_text="Unique identifier for the credential"
    )
    public_key = models.TextField(
        help_text="Public key for verifying signatures"
    )
    sign_count = models.IntegerField(
        default=0,
        help_text="Number of times this credential has been used"
    )
    device_name = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Name of the device (e.g., iPhone 12, Laptop)"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser/device user agent"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address at registration time"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this credential is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Biometric Credential"
        verbose_name_plural = "Biometric Credentials"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['credential_id']),
            models.Index(fields=['-last_used']),
        ]
    
    def __str__(self):
        device = self.device_name or 'Unknown Device'
        return f"{self.user.username} - {device} ({self.created_at.strftime('%Y-%m-%d')})"
    
    def update_sign_count(self, new_count):
        """Update sign count for the credential"""
        if new_count > self.sign_count:
            self.sign_count = new_count
            self.last_used = timezone.now()
            self.save(update_fields=['sign_count', 'last_used'])
            return True
        return False
    
    def mark_used(self):
        """Mark credential as used without updating sign count"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])
    
    def deactivate(self):
        """Deactivate this credential"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def activate(self):
        """Activate this credential"""
        self.is_active = True
        self.save(update_fields=['is_active'])
    
    @property
    def is_expired(self):
        """Check if credential has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def credential_id_b64(self):
        """Get base64 encoded credential ID"""
        try:
            return base64.b64encode(self.credential_id.encode()).decode()
        except:
            return self.credential_id
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'credential_id': self.credential_id[:20] + '...' if len(self.credential_id) > 20 else self.credential_id,
            'device_name': self.device_name or 'Unknown',
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'sign_count': self.sign_count
        }
    
    @classmethod
    def get_active_credentials(cls, user):
        """Get active credentials for a user"""
        return cls.objects.filter(user=user, is_active=True)
    
    @classmethod
    def get_credential_by_id(cls, credential_id):
        """Get credential by ID"""
        try:
            return cls.objects.get(credential_id=credential_id, is_active=True)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def create_from_webauthn(cls, user, credential_data, request=None):
        """Create a credential from WebAuthn registration data"""
        credential_id = credential_data.get('id')
        public_key = credential_data.get('publicKey') or json.dumps(credential_data.get('response', {}))
        device_name = credential_data.get('device_name', 'WebAuthn Device')
        
        if not credential_id:
            raise ValueError("Credential ID is required")
        
        credential = cls.objects.create(
            user=user,
            credential_id=credential_id,
            public_key=public_key,
            device_name=device_name,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            is_active=True
        )
        
        return credential
    
    @classmethod
    def delete_all_for_user(cls, user):
        """Delete all credentials for a user"""
        deleted, _ = cls.objects.filter(user=user).delete()
        return deleted