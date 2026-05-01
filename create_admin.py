import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bantu_books.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email = "admin@bantubooks.com"
password = "Admin123!"

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        username='admin',
        email=email,
        password=password,
        first_name='Admin',
        last_name='User'
    )
    print(f"Superuser created successfully! Email: {email}, Password: {password}")
else:
    print("Superuser already exists!")