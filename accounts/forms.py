from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from .models import User
import re


class UserRegistrationForm(UserCreationForm):
    """
    Enhanced form for user registration with validation
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'your@email.com',
            'autocomplete': 'off'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?260?\d{9}$',
                message='Enter a valid Zambian phone number (e.g., +260977123456 or 0977123456)'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': '+260977123456'
        })
    )
    province = forms.ChoiceField(
        choices=User.PROVINCE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        validators=[MinLengthValidator(2, 'First name must be at least 2 characters')],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        validators=[MinLengthValidator(2, 'Last name must be at least 2 characters')],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Last name'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 
                  'province', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style username field
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Choose a username'
        })
        
        # Style password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Confirm your password'
        })
        
        # Add help text for password
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters and cannot be entirely numeric.'
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('This username is already taken. Please choose another.')
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('Username can only contain letters, numbers, and @/./+/-/_ characters.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        # Normalize phone number to start with +260
        if phone.startswith('0'):
            phone = '+260' + phone[1:]
        elif not phone.startswith('+'):
            phone = '+260' + phone
        
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError('A user with this phone number already exists.')
        return phone
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if password1.isdigit():
            raise ValidationError('Password cannot be entirely numeric.')
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.phone_number = self.cleaned_data['phone_number']
        user.province = self.cleaned_data['province']
        user.user_type = 'basic'
        
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    """
    Enhanced form for user login with remember me functionality
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Username or Email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Password'
        })
    )
    remember_me = forms.BooleanField(required=False, initial=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['remember_me'].widget.attrs.update({
            'class': 'mr-2'
        })
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Try to authenticate with email if username not found
            user = None
            if '@' in username:
                try:
                    user_obj = User.objects.get(email__iexact=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if not user:
                user = authenticate(username=username, password=password)
            
            if not user:
                raise ValidationError('Invalid username or password. Please try again.')
            
            if not user.is_active:
                raise ValidationError('This account is inactive. Please contact support.')
            
            self.user_cache = user
        
        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    """
    Enhanced form for updating user profile with validation
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'your@email.com'
        })
    )
    phone_number = forms.CharField(
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?260?\d{9}$',
                message='Enter a valid Zambian phone number (e.g., +260977123456)'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': '+260977123456'
        })
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'province', 
                  'district', 'constituency', 'school_or_work', 'bio', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'Last name'
            }),
            'province': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent'
            }),
            'district': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'e.g., Lusaka'
            }),
            'constituency': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'e.g., Munali'
            }),
            'school_or_work': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'School, College, or Workplace'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'accept': 'image/*'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.exclude(id=self.instance.id).filter(email__iexact=email).exists():
            raise ValidationError('This email is already in use by another account.')
        return email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Normalize phone number
            if phone.startswith('0'):
                phone = '+260' + phone[1:]
            elif phone and not phone.startswith('+'):
                phone = '+260' + phone
            
            if User.objects.exclude(id=self.instance.id).filter(phone_number=phone).exists():
                raise ValidationError('This phone number is already in use by another account.')
        return phone
    
    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            # Validate file size (max 5MB)
            if picture.size > 5 * 1024 * 1024:
                raise ValidationError('Profile picture must be less than 5MB.')
            
            # Validate file type
            content_type = getattr(picture, 'content_type', '')
            if content_type and content_type not in ['image/jpeg', 'image/png', 'image/gif']:
                raise ValidationError('Only JPEG, PNG, and GIF images are allowed.')
        
        return picture


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Enhanced password change form
    """
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Current password'
        })
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'New password'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Confirm new password'
        })
    )
    
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if len(password1) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if password1.isdigit():
            raise ValidationError('Password cannot be entirely numeric.')
        return password1


class CustomSetPasswordForm(SetPasswordForm):
    """
    Enhanced set password form for password reset
    """
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'New password'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
            'placeholder': 'Confirm new password'
        })
    )