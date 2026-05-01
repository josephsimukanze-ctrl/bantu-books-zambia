import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bantu_books.settings')
django.setup()

from dictionary.models import DictionaryWord
from django.utils.text import slugify
import nltk
from nltk.corpus import wordnet

# Download required NLTK data
print("📚 Downloading NLTK word data...")
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

print("📖 Loading words from WordNet...")

count = 0
skipped = 0

# Get all wordnet synsets (words with definitions)
for synset in list(wordnet.all_synsets())[:3000]:  # Import first 3000 words
    word = synset.lemmas()[0].name().replace('_', ' ')
    definition = synset.definition()
    
    # Skip long words or words with special characters
    if len(word) > 25 or not word.replace(' ', '').isalpha():
        skipped += 1
        continue
    
    # Map part of speech
    pos_map = {'n': 'noun', 'v': 'verb', 'a': 'adjective', 'r': 'adverb'}
    part_of_speech = pos_map.get(synset.pos(), 'noun')
    
    # Check if word already exists
    if not DictionaryWord.objects.filter(word__iexact=word).exists():
        try:
            DictionaryWord.objects.create(
                word=word.title(),
                slug=slugify(word),
                definition=definition[:500],  # Limit definition length
                part_of_speech=part_of_speech,
                is_active=True
            )
            count += 1
            if count % 100 == 0:
                print(f"  Progress: {count} words imported...")
        except Exception as e:
            skipped += 1
    else:
        skipped += 1

print(f"\n✅ Successfully imported {count} words with definitions!")
print(f"⚠️ Skipped {skipped} words")
print(f"📚 Total words in dictionary: {DictionaryWord.objects.count()}")