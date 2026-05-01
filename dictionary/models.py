# dictionary/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify

class DictionaryWord(models.Model):
    """Dictionary word entries"""
    word = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(unique=True, blank=True)
    
    # Word details
    definition = models.TextField()
    part_of_speech = models.CharField(max_length=50, blank=True, 
        choices=[
            ('noun', 'Noun'),
            ('verb', 'Verb'),
            ('adjective', 'Adjective'),
            ('adverb', 'Adverb'),
            ('preposition', 'Preposition'),
            ('conjunction', 'Conjunction'),
            ('interjection', 'Interjection'),
        ])
    
    # Examples and usage
    example_sentence = models.TextField(blank=True, help_text="Example sentence using the word")
    synonyms = models.TextField(blank=True, help_text="Comma-separated synonyms")
    antonyms = models.TextField(blank=True, help_text="Comma-separated antonyms")
    
    # Additional info
    pronunciation = models.CharField(max_length=100, blank=True, help_text="Phonetic pronunciation")
    origin = models.CharField(max_length=100, blank=True, help_text="Word origin/etymology")
    
    # Zambian context
    is_zambian_term = models.BooleanField(default=False, help_text="Is this a Zambian/local term?")
    local_usage = models.TextField(blank=True, help_text="How this word is used in Zambia")
    
    # Media
    audio_pronunciation = models.FileField(upload_to='dictionary/audio/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['word']
        verbose_name = "Dictionary Word"
        verbose_name_plural = "Dictionary Words"
        indexes = [
            models.Index(fields=['word']),
            models.Index(fields=['is_zambian_term']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.word)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.word
    
    @property
    def synonym_list(self):
        return [s.strip() for s in self.synonyms.split(',')] if self.synonyms else []
    
    @property
    def antonym_list(self):
        return [a.strip() for a in self.antonyms.split(',')] if self.antonyms else []


class UserWordHistory(models.Model):
    """Track words users look up"""
    # FIX: Use settings.AUTH_USER_MODEL instead of 'auth.User'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='word_history')
    word = models.ForeignKey(DictionaryWord, on_delete=models.CASCADE)
    looked_up_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-looked_up_at']
        verbose_name = "User Word History"
        verbose_name_plural = "User Word Histories"
    
    def __str__(self):
        return f"{self.user.username} looked up '{self.word.word}'"