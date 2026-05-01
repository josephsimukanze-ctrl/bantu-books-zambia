import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bantu_books.settings')
django.setup()

from dictionary.models import DictionaryWord
from django.utils.text import slugify

# Read words from file
with open('words.txt', 'r') as f:
    words = f.read().splitlines()

count = 0
for word in words[:1000]:  # Add first 1000 words
    if len(word) > 3 and len(word) < 20:  # Filter reasonable length
        if not DictionaryWord.objects.filter(word__iexact=word).exists():
            DictionaryWord.objects.create(
                word=word.capitalize(),
                slug=slugify(word),
                definition=f"Definition of {word} - Add real definition here",
                is_active=True
            )
            count += 1
            if count % 100 == 0:
                print(f"Added {count} words...")

print(f"Done! Added {count} words.")