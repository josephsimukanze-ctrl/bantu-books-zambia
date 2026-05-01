import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bantu_books.settings')
django.setup()

from dictionary.models import DictionaryWord
from django.utils.text import slugify

# Educational words for Zambian students
words_data = [
    # Academic Terms
    ('Education', 'The process of receiving or giving systematic instruction', 'noun'),
    ('Learning', 'The acquisition of knowledge or skills through study', 'noun'),
    ('Knowledge', 'Facts, information, and skills acquired through experience or education', 'noun'),
    ('Study', 'The devotion of time and attention to acquiring knowledge', 'noun'),
    ('School', 'An institution for educating children', 'noun'),
    ('Teacher', 'A person who teaches, especially in a school', 'noun'),
    ('Student', 'A person who is studying at a school or college', 'noun'),
    ('Book', 'A written or printed work consisting of pages glued or sewn together', 'noun'),
    ('Read', 'Look at and comprehend the meaning of written matter', 'verb'),
    ('Write', 'Mark letters, words, or other symbols on a surface', 'verb'),
    ('Mathematics', 'The abstract science of number, quantity, and space', 'noun'),
    ('Science', 'The systematic study of the structure of the physical world', 'noun'),
    ('Biology', 'The study of living organisms', 'noun'),
    ('Chemistry', 'The branch of science concerned with substances and their properties', 'noun'),
    ('Physics', 'The branch of science concerned with matter and energy', 'noun'),
    ('History', 'The study of past events', 'noun'),
    ('Geography', 'The study of the physical features of the earth', 'noun'),
    ('English', 'The language of England, widely used around the world', 'noun'),
    ('Literature', 'Written works of superior or lasting artistic merit', 'noun'),
    
    # Zambian Terms
    ('ECZ', 'Examinations Council of Zambia - responsible for national exams', 'noun', True),
    ('Bemba', 'One of the major local languages in Zambia', 'noun', True),
    ('Nyanja', 'One of the major local languages in Zambia', 'noun', True),
    ('Tonga', 'One of the major local languages in Zambia', 'noun', True),
    ('Lozi', 'One of the major local languages in Zambia', 'noun', True),
    ('Zambia', 'A country in Southern Africa', 'noun', True),
    ('Lusaka', 'The capital city of Zambia', 'noun', True),
    ('Ubuntu', 'African philosophy of humanity and community', 'noun', True),
    
    # Study Skills
    ('Analyze', 'Examine something methodically', 'verb'),
    ('Evaluate', 'Form an idea of the value or amount of something', 'verb'),
    ('Summarize', 'Give a brief statement of the main points', 'verb'),
    ('Interpret', 'Explain the meaning of information', 'verb'),
    ('Demonstrate', 'Show clearly the existence or truth of something', 'verb'),
    ('Research', 'Systematic investigation to establish facts', 'noun'),
    ('Assignment', 'A task given to students', 'noun'),
    ('Homework', 'Schoolwork done at home', 'noun'),
    ('Examination', 'A formal test of knowledge', 'noun'),
    ('Grade', 'A mark indicating the quality of work', 'noun'),
]

print("📚 Adding words to dictionary...")

count = 0
for word_data in words_data:
    word = word_data[0]
    definition = word_data[1]
    part_of_speech = word_data[2]
    is_zambian = word_data[3] if len(word_data) > 3 else False
    
    # Check if word already exists
    existing = DictionaryWord.objects.filter(word__iexact=word).first()
    if existing:
        print(f"⚠️ Word already exists: {word}")
        continue
    
    # Create new word
    DictionaryWord.objects.create(
        word=word,
        slug=slugify(word),
        definition=definition,
        part_of_speech=part_of_speech,
        is_zambian_term=is_zambian,
        is_active=True
    )
    count += 1
    print(f"✓ Added: {word}")

print(f"\n✅ Successfully added {count} words to the dictionary!")
print(f"Total words now: {DictionaryWord.objects.count()}")