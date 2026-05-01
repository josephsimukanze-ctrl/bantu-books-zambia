# dictionary/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import DictionaryWord, UserWordHistory
import difflib

def dictionary_home(request):
    """Dictionary home page with word search and letter filtering"""
    query = request.GET.get('q', '').strip()
    letter = request.GET.get('letter', '').strip().upper()
    
    # Start with all active words
    words = DictionaryWord.objects.filter(is_active=True)
    
    # Apply letter filter
    if letter and len(letter) == 1:
        words = words.filter(word__istartswith=letter)
        active_letter = letter
    else:
        active_letter = ''
    
    # Apply search query
    suggestions = []
    if query:
        # Search in word and definition
        words = words.filter(
            Q(word__icontains=query) |
            Q(definition__icontains=query)
        )
        
        # Debug print
        print(f"Searching for '{query}', found {words.count()} results")
        
        # If no results, get suggestions
        if not words.exists():
            all_words = list(DictionaryWord.objects.filter(is_active=True).values_list('word', flat=True))
            suggestions = difflib.get_close_matches(query, all_words, n=5, cutoff=0.6)
    
    # Order alphabetically
    words = words.order_by('word')
    
    # Pagination
    paginator = Paginator(words, 20)
    page = request.GET.get('page', 1)
    words_page = paginator.get_page(page)
    
    # Alphabet for filtering
    alphabet = [chr(i) for i in range(65, 91)]  # A-Z
    
    context = {
        'words': words_page,
        'query': query,
        'active_letter': active_letter,
        'alphabet': alphabet,
        'total_words': DictionaryWord.objects.filter(is_active=True).count(),
        'total_results': words.count(),
        'suggestions': suggestions,
    }
    return render(request, 'dictionary/home.html', context)


def word_detail(request, slug):
    """View details of a specific word"""
    word = get_object_or_404(DictionaryWord, slug=slug, is_active=True)
    
    # Increment view count
    word.views_count += 1
    word.save(update_fields=['views_count'])
    
    # Track user history if logged in
    if request.user.is_authenticated:
        UserWordHistory.objects.get_or_create(
            user=request.user,
            word=word
        )
    
    # Get related words
    related_words = DictionaryWord.objects.filter(
        word__istartswith=word.word[0],
        is_active=True
    ).exclude(id=word.id)[:10]
    
    context = {
        'word': word,
        'related_words': related_words,
    }
    return render(request, 'dictionary/word_detail.html', context)


@login_required
def word_history(request):
    """User's word lookup history"""
    history = UserWordHistory.objects.filter(
        user=request.user
    ).select_related('word').order_by('-looked_up_at')
    
    paginator = Paginator(history, 20)
    page = request.GET.get('page', 1)
    history_page = paginator.get_page(page)
    
    context = {
        'history': history_page,
        'total_lookups': history.count(),
    }
    return render(request, 'dictionary/history.html', context)


# Add this to dictionary/views.py if not already there

def api_lookup_word(request):
    """API endpoint for quick word lookup (AJAX)"""
    word_text = request.GET.get('word', '').strip().lower()
    
    if not word_text:
        return JsonResponse({'error': 'No word provided', 'found': False}, status=400)
    
    try:
        word = DictionaryWord.objects.get(word__iexact=word_text, is_active=True)
        
        data = {
            'found': True,
            'word': word.word,
            'definition': word.definition,
            'part_of_speech': word.get_part_of_speech_display() if word.part_of_speech else '',
            'example_sentence': word.example_sentence,
            'is_zambian_term': word.is_zambian_term,
        }
        return JsonResponse(data)
        
    except DictionaryWord.DoesNotExist:
        return JsonResponse({'found': False, 'word': word_text, 'error': 'Word not found'})
        
    except DictionaryWord.DoesNotExist:
        # Get suggestions
        suggestions = DictionaryWord.objects.filter(
            Q(word__icontains=word_text) |
            Q(word__istartswith=word_text[:3]),
            is_active=True
        ).values_list('word', flat=True)[:5]
        
        return JsonResponse({
            'found': False, 
            'word': word_text, 
            'error': 'Word not found',
            'suggestions': list(suggestions)
        })


def api_suggest_words(request):
    """API endpoint for word suggestions (autocomplete)"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    suggestions = DictionaryWord.objects.filter(
        Q(word__istartswith=query),
        is_active=True
    ).values_list('word', flat=True)[:10]
    
    return JsonResponse({'suggestions': list(suggestions)})