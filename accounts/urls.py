from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # ============ AUTHENTICATION ============
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    
    # ============ PROFILE & SETTINGS ============
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('security/', views.security_settings, name='account_security'),
    
    # ============ SUBSCRIPTION & UPGRADE ============
    path('upgrade/', views.upgrade_account_view, name='upgrade'),
    path('subscription/', views.subscription_dashboard, name='subscription_dashboard'),
    
    # ============ PAYMENT PROCESSING ============
    path('process-payment/', views.process_upgrade_payment, name='process_upgrade_payment'),
    path('verify-payment/<str:transaction_id>/', views.verify_payment, name='verify_payment'),
    path('payment-status/', views.get_payment_status, name='payment_status'),
    
    # ============ HISTORY ============
    path('download-history/', views.download_history_view, name='download_history'),
    path('reading-history/', views.reading_history_view, name='reading_history'),
    
    # ============ BIOMETRIC AUTHENTICATION ============
    path('biometric/status/', views.get_biometric_status, name='biometric_status'),
    path('biometric/credentials/', views.get_biometric_credentials, name='biometric_credentials'),
    path('biometric/login-challenge/', views.biometric_login_challenge, name='biometric_login_challenge'),
    path('biometric/verify-login/', views.biometric_verify_login, name='biometric_verify_login'),
    
    # These require login
    path('biometric/register/', views.register_biometric, name='register_biometric'),
    path('biometric/remove/', views.remove_biometric, name='remove_biometric'),
    path('biometric/login/', views.biometric_login, name='biometric_login'),
    
    # ============ TWO-FACTOR AUTHENTICATION ============
    path('enable-2fa/', views.enable_2fa, name='enable_2fa'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),
    path('qrcode/', views.qrcode_view, name='qrcode'),
    path('generate-backup-codes/', views.generate_backup_codes, name='generate_backup_codes'),

    # ============ ADMIN SUBSCRIPTION MANAGEMENT ============
    path('admin/subscriptions/', views.admin_subscription_dashboard, name='admin_subscription_dashboard'),
    path('admin/payments/', views.admin_subscription_payments, name='admin_subscription_payments'),
    path('admin/payment/update/<str:transaction_id>/', views.admin_update_payment_status, name='admin_update_payment_status'),
    path('admin/plans/', views.admin_subscription_plans, name='admin_subscription_plans'),
    path('admin/cancel-subscription/<int:user_id>/', views.admin_cancel_subscription, name='admin_cancel_subscription'),
    path('admin/export-data/', views.export_subscription_data, name='export_subscription_data'),
    path('admin-panel/', views.admin_subscription_dashboard, name='admin_panel'),
]