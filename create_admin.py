import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bantu_books.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# First, delete existing admin if exists
User.objects.filter(username='admin').delete()
User.objects.filter(email='admin@bantubooks.com').delete()

# Create new superuser
email = "admin@bantubooks.com"
password = "Admin@Bantu2026!"

user = User.objects.create_superuser(
    username='admin',
    email=email,
    password=password,
    first_name='Admin',
    last_name='User',
    is_active=True
)

print(f"✅ Superuser created successfully!")
print(f"   Username: admin")
print(f"   Email: {email}")
print(f"   Password: {password}")
print(f"   Login at: https://bantu-books-zambia.onrender.com/admin")