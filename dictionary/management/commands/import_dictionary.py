import json
import csv
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from dictionary.models import DictionaryWord
import requests

class Command(BaseCommand):
    help = 'Import dictionary words from various sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='api',
            help='Source of dictionary data (api, csv, json)'
        )

    def handle(self, *args, **options):
        source = options['source']
        
        if source == 'api':
            self.import_from_api()
        elif source == 'csv':
            self.import_from_csv()
        else:
            self.create_sample_words()
    
    def import_from_api(self):
        """Import words from a free dictionary API"""
        self.stdout.write("📚 Importing words from dictionary API...")
        
        # List of common words to import
        common_words = [
            'education', 'learning', 'school', 'teacher', 'student', 'book', 'read',
            'write', 'mathematics', 'science', 'english', 'history', 'geography',
            'biology', 'chemistry', 'physics', 'computer', 'library', 'knowledge',
            'study', 'exam', 'test', 'grade', 'class', 'university', 'college',
            'zambia', 'africa', 'culture', 'language', 'english', 'bemba', 'nyanja',
            'success', 'achieve', 'excellent', 'brilliant', 'intelligent', 'smart',
            'dedication', 'motivation', 'inspiration', 'determination', 'persistence',
            'develop', 'improve', 'enhance', 'advance', 'progress', 'growth',
            'opportunity', 'challenge', 'solution', 'answer', 'question', 'explain'
        ]
        
        words_added = 0
        words_failed = 0
        
        for word in common_words:
            try:
                # Use Free Dictionary API
                response = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}')
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        # Extract definition
                        meanings = data[0].get('meanings', [])
                        if meanings:
                            definition = meanings[0].get('definitions', [{}])[0].get('definition', 'No definition available')
                            part_of_speech = meanings[0].get('partOfSpeech', '')
                            example = meanings[0].get('definitions', [{}])[0].get('example', '')
                            
                            # Check if word already exists
                            if not DictionaryWord.objects.filter(word__iexact=word).exists():
                                DictionaryWord.objects.create(
                                    word=word.capitalize(),
                                    slug=slugify(word),
                                    definition=definition[:500],
                                    part_of_speech=part_of_speech,
                                    example_sentence=example[:200] if example else '',
                                    is_active=True
                                )
                                words_added += 1
                                self.stdout.write(self.style.SUCCESS(f'  ✓ Added: {word}'))
                            else:
                                self.stdout.write(self.style.WARNING(f'  ⚠ Skipped (exists): {word}'))
                    else:
                        words_failed += 1
                else:
                    words_failed += 1
                    
            except Exception as e:
                words_failed += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Failed: {word} - {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Import complete! Added {words_added} words. Failed: {words_failed}'))
    
    def import_from_csv(self):
        """Import words from a CSV file"""
        self.stdout.write("📚 Please provide a CSV file with columns: word, definition, part_of_speech")
        self.stdout.write("Example: word,definition,part_of_speech")
        self.stdout.write("Place the file at: dictionary/data/words.csv")
        
        import os
        csv_path = 'dictionary/data/words.csv'
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_path}'))
            self.create_sample_csv()
            return
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                word = row.get('word', '').strip()
                definition = row.get('definition', '').strip()
                part_of_speech = row.get('part_of_speech', '')
                
                if word and definition:
                    if not DictionaryWord.objects.filter(word__iexact=word).exists():
                        DictionaryWord.objects.create(
                            word=word.capitalize(),
                            slug=slugify(word),
                            definition=definition,
                            part_of_speech=part_of_speech,
                            is_active=True
                        )
                        count += 1
                        self.stdout.write(f'  ✓ Added: {word}')
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Added {count} words from CSV!'))
    
    def create_sample_csv(self):
        """Create a sample CSV template"""
        import os
        os.makedirs('dictionary/data', exist_ok=True)
        
        sample_words = [
            ['word', 'definition', 'part_of_speech'],
            ['Abundant', 'Existing or available in large quantities', 'adjective'],
            ['Achieve', 'Successfully bring about or reach a desired objective', 'verb'],
            ['Brilliant', 'Exceptionally clever or talented', 'adjective'],
            ['Challenge', 'A call to take part in a contest or competition', 'noun'],
            ['Dedication', 'The quality of being committed to a task', 'noun'],
        ]
        
        with open('dictionary/data/words.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(sample_words)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Sample CSV created at: dictionary/data/words.csv'))
        self.stdout.write("Edit this file and run: python manage.py import_dictionary --source=csv")
    
    def create_sample_words(self):
        """Create sample Zambian educational words"""
        self.stdout.write("📚 Creating sample Zambian educational words...")
        
        words_data = [
            # Educational Terms
            {'word': 'ECZ', 'definition': 'Examinations Council of Zambia - the body responsible for national examinations in Zambia', 'part_of_speech': 'noun', 'is_zambian_term': True},
            {'word': 'Curriculum', 'definition': 'The subjects comprising a course of study in a school or college', 'part_of_speech': 'noun'},
            {'word': 'Examination', 'definition': 'A formal test of a student\'s knowledge or proficiency in a subject', 'part_of_speech': 'noun'},
            {'word': 'Mathematics', 'definition': 'The abstract science of number, quantity, and space', 'part_of_speech': 'noun'},
            {'word': 'Science', 'definition': 'The systematic study of the structure and behavior of the physical world', 'part_of_speech': 'noun'},
            {'word': 'Literature', 'definition': 'Written works, especially those considered of superior or lasting artistic merit', 'part_of_speech': 'noun'},
            {'word': 'Biology', 'definition': 'The study of living organisms', 'part_of_speech': 'noun'},
            {'word': 'Chemistry', 'definition': 'The branch of science concerned with the substances of which matter is composed', 'part_of_speech': 'noun'},
            {'word': 'Physics', 'definition': 'The branch of science concerned with the nature and properties of matter and energy', 'part_of_speech': 'noun'},
            {'word': 'Geography', 'definition': 'The study of the physical features of the earth and its atmosphere', 'part_of_speech': 'noun'},
            {'word': 'History', 'definition': 'The study of past events, particularly in human affairs', 'part_of_speech': 'noun'},
            
            # Zambian Terms
            {'word': 'Bemba', 'definition': 'One of the major local languages spoken in Zambia', 'part_of_speech': 'noun', 'is_zambian_term': True},
            {'word': 'Nyanja', 'definition': 'One of the major local languages spoken in Zambia', 'part_of_speech': 'noun', 'is_zambian_term': True},
            {'word': 'Tonga', 'definition': 'One of the major local languages spoken in Zambia', 'part_of_speech': 'noun', 'is_zambian_term': True},
            {'word': 'Lozi', 'definition': 'One of the major local languages spoken in Zambia', 'part_of_speech': 'noun', 'is_zambian_term': True},
            {'word': 'Ubuntu', 'definition': 'A traditional African philosophy emphasizing community and mutual caring', 'part_of_speech': 'noun', 'is_zambian_term': True},
            
            # Common Academic Words
            {'word': 'Analyze', 'definition': 'Examine methodically and in detail the constitution or structure of something', 'part_of_speech': 'verb'},
            {'word': 'Evaluate', 'definition': 'Form an idea of the amount, number, or value of; assess', 'part_of_speech': 'verb'},
            {'word': 'Summarize', 'definition': 'Give a brief statement of the main points of something', 'part_of_speech': 'verb'},
            {'word': 'Interpret', 'definition': 'Explain the meaning of information or actions', 'part_of_speech': 'verb'},
            {'word': 'Demonstrate', 'definition': 'Clearly show the existence or truth of something by giving proof or evidence', 'part_of_speech': 'verb'},
        ]
        
        count = 0
        for word_data in words_data:
            word_name = word_data['word']
            if not DictionaryWord.objects.filter(word__iexact=word_name).exists():
                DictionaryWord.objects.create(
                    word=word_name,
                    slug=slugify(word_name),
                    definition=word_data['definition'],
                    part_of_speech=word_data['part_of_speech'],
                    is_zambian_term=word_data.get('is_zambian_term', False),
                    is_active=True
                )
                count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Added: {word_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠ Skipped (exists): {word_name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Added {count} sample words!'))