import os
import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from dictionary.models import DictionaryWord

class Command(BaseCommand):
    help = 'Import words from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='words.json',
            help='Path to JSON file'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5000,
            help='Number of words to import'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        limit = options['limit']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        
        self.stdout.write(f"📚 Loading dictionary from {file_path}...")
        
        with open(file_path, 'r') as f:
            words_dict = json.load(f)
        
        self.stdout.write(f"📖 Found {len(words_dict)} words in the file")
        
        count = 0
        skipped = 0
        
        for word, definition in list(words_dict.items())[:limit]:
            # Filter valid words
            if len(word) > 30 or not word.replace('_', '').isalpha():
                skipped += 1
                continue
            
            # Skip if already exists
            if DictionaryWord.objects.filter(word__iexact=word).exists():
                skipped += 1
                continue
            
            try:
                DictionaryWord.objects.create(
                    word=word.lower().capitalize(),
                    slug=slugify(word),
                    definition=f'A common English word: {word}',
                    part_of_speech='noun',
                    is_active=True
                )
                count += 1
                
                if count % 500 == 0:
                    self.stdout.write(f"  Progress: {count} words imported...")
                    
            except Exception as e:
                skipped += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully imported {count} words!'))
        self.stdout.write(self.style.WARNING(f'⚠️ Skipped {skipped} words'))
        self.stdout.write(f'📚 Total words in dictionary: {DictionaryWord.objects.count()}')