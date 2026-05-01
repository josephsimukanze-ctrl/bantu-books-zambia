# payments/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class PaymentMethod(models.Model):
    """Payment methods"""
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Payment transactions"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('pending_verification', 'Pending Verification'),
        ('pending_payment', 'Pending Payment'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    plan_type = models.CharField(max_length=20)  # monthly, quarterly, yearly, lifetime
    payment_method = models.CharField(max_length=20)  # airtel, mtn, zamtel, bank
    payment_details = models.JSONField(default=dict, help_text="Payment-specific details")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference_number = models.CharField(max_length=100, blank=True)
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user.email} - {self.amount} - {self.status}"