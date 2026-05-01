import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bantu_books.settings')
django.setup()

from dictionary.models import DictionaryWord
from django.utils.text import slugify

print("📚 Loading dictionary from words.json...")

# Load the JSON file
with open('words.json', 'r') as f:
    words_dict = json.load(f)

print(f"📖 Found {len(words_dict)} words in the file")

count = 0
skipped = 0

# Import first 5000 words (you can adjust this number)
for word, definition in list(words_dict.items())[:5000]:
    # Skip words that are too long or have special characters
    if len(word) > 30 or not word.isalpha():
        skipped += 1
        continue
    
    # Check if word already exists
    if not DictionaryWord.objects.filter(word__iexact=word).exists():
        try:
            DictionaryWord.objects.create(
                word=word.lower().capitalize(),
                slug=slugify(word),
                definition=f'A common English word: {word}',
                part_of_speech='noun',  # Default part of speech
                is_active=True
            )
            count += 1
            if count % 500 == 0:
                print(f"  Progress: {count} words imported...")
        except Exception as e:
            skipped += 1
    else:
        skipped += 1

print(f"\n✅ Successfully imported {count} words!")
print(f"⚠️ Skipped {skipped} words (already exist or invalid)")
print(f"📚 Total words in dictionary: {DictionaryWord.objects.count()}")