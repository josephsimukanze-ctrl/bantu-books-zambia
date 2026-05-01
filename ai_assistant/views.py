# ai_assistant/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
import json
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)

# Configure AI - Google Gemini (Free)
try:
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    GEMINI_AVAILABLE = True
    logger.info("✅ Google Gemini AI is available")
except Exception as e:
    GEMINI_AVAILABLE = False
    logger.warning(f"⚠️ Google Gemini AI not available: {e}")


def ai_assistant_home(request):
    """AI Assistant chat interface"""
    # Track daily usage
    today = datetime.now().date().isoformat()
    usage_key = f'ai_usage_{today}'
    usage_count = request.session.get(usage_key, 0)
    
    context = {
        'has_ai': GEMINI_AVAILABLE,
        'usage_count': usage_count,
        'remaining': max(0, 100 - usage_count),  # Free tier: 100 requests/day
        'show_welcome': not request.session.get('has_seen_welcome', False),
    }
    
    # Mark welcome as seen
    if not request.session.get('has_seen_welcome', False):
        request.session['has_seen_welcome'] = True
    
    return render(request, 'ai_assistant/chat.html', context)


@csrf_exempt
def ai_chat_api(request):
    """API endpoint for AI chat with rate limiting and fallback"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    # Rate limiting - 100 requests per day per user/session
    today = datetime.now().date().isoformat()
    usage_key = f'ai_usage_{today}'
    usage_count = request.session.get(usage_key, 0)
    
    if usage_count >= 100:
        return JsonResponse({
            'success': False,
            'error': 'Daily limit reached (100 questions). Please try again tomorrow!',
            'limit_reached': True
        }, status=429)
    
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        
        if not question:
            return JsonResponse({'error': 'No question provided'}, status=400)
        
        # Increment usage counter
        request.session[usage_key] = usage_count + 1
        
        # Log the question for analytics
        logger.info(f"AI Question: {question[:100]}...")
        
        # Zambian educational context
        system_prompt = """You are "Bantu AI" - an educational assistant for Bantu Books Zambia, a Zambian digital library platform.

🎯 Your Role:
- Help Zambian students with book summaries, explanations, and study tips
- Answer questions about ECZ exams and Zambian curriculum
- Provide definitions and word explanations
- Offer study techniques and learning strategies
- Be friendly, encouraging, and culturally appropriate

📚 Zambian Context:
- ECZ = Examinations Council of Zambia (national exams at Grades 7, 9, 12)
- 10 Provinces: Lusaka, Copperbelt, Southern, Central, Eastern, Western, Northern, North-Western, Luapula, Muchinga
- Subjects: English, Mathematics, Science, Social Studies, Zambian Languages
- Local languages: Bemba, Nyanja, Tonga, Lozi, Kaonde, Lunda

💡 Guidelines:
- Keep responses concise (2-3 paragraphs max)
- Use simple, clear language suitable for students
- Be accurate and helpful
- If unsure, admit it and suggest checking the library
- Encourage further reading from Bantu Books Zambia
- Use emojis occasionally to make responses friendly

Remember: You're helping Zambian students succeed!"""

        # Use Gemini if available
        if GEMINI_AVAILABLE:
            try:
                model = genai.GenerativeModel('gemini-pro')
                full_prompt = f"{system_prompt}\n\nUser question: {question}\n\nAssistant response:"
                response = model.generate_content(full_prompt)
                answer = response.text
                
                # Log success
                logger.info(f"✅ Gemini response generated successfully")
                
            except Exception as gemini_error:
                logger.error(f"Gemini error: {gemini_error}")
                answer = get_intelligent_fallback(question)
        else:
            # Use intelligent fallback responses
            answer = get_intelligent_fallback(question)
        
        return JsonResponse({
            'success': True,
            'answer': answer,
            'question': question,
            'remaining': 100 - (usage_count + 1),
            'using_ai': GEMINI_AVAILABLE
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"AI Chat Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def get_intelligent_fallback(question):
    """Intelligent fallback responses when AI is unavailable"""
    q = question.lower()
    
    # ECZ Exam Questions
    if 'ecz' in q:
        return """📚 **About ECZ (Examinations Council of Zambia)**

ECZ conducts national examinations for:
- 🎓 **Grade 7** (Primary School Leaving Exam)
- 🎓 **Grade 9** (Junior Secondary Certificate)
- 🎓 **Grade 12** (School Certificate)

**How to prepare:**
1. Practice past papers (available in our library!)
2. Understand the exam format
3. Time yourself during practice
4. Review weak areas
5. Join study groups

**Find ECZ materials in our library under "ECZ Exam Papers" category!**

Would you like tips for a specific grade?"""

    # Study Tips
    elif any(word in q for word in ['study', 'prepare', 'learn', 'revise']):
        return """📖 **Effective Study Techniques**

**1. Pomodoro Technique**
- Study for 25 minutes
- Take 5-minute break
- Repeat 4 times, then take longer break

**2. Active Recall**
- Test yourself instead of just reading
- Use flashcards
- Explain concepts to someone else

**3. Spaced Repetition**
- Review material after 1 day, 3 days, 1 week
- Focus on what you don't know

**4. Practice Past Papers**
- Available in our ECZ section!
- Simulate exam conditions

**Pro tip:** Create a study schedule and stick to it! 📅

Need help with a specific subject?"""

    # Mathematics
    elif 'math' in q or 'mathematics' in q:
        return """🧮 **Mathematics Study Guide**

**Key Topics for ECZ:**
- Algebra (equations, inequalities)
- Geometry (angles, shapes, theorems)
- Trigonometry (sine, cosine, tangent)
- Statistics (mean, median, mode)
- Probability

**Study Tips:**
✅ Practice daily - Math requires regular practice
✅ Memorize formulas - Create formula cards
✅ Show your work - Get partial credit
✅ Check our ECZ Math past papers
✅ Focus on word problems

**Available in our library:**
- ECZ Mathematics past papers (Grade 9 & 12)
- Step-by-step solutions
- Practice exercises

What math topic are you struggling with?"""

    # English
    elif 'english' in q or 'vocabulary' in q:
        return """📝 **English Language Tips**

**To Improve Your English:**

**Reading:** 📖
- Read daily from our library books
- Start with shorter texts
- Note new vocabulary words

**Writing:** ✍️
- Practice essay writing
- Get feedback from teachers
- Use our dictionary for word meanings

**Speaking:** 🗣️
- Practice with friends
- Record yourself speaking
- Join English clubs

**Grammar:** 📚
- Focus on tenses
- Learn common mistakes
- Use grammar exercises

**Vocabulary:** 🔤
- Learn 5 new words daily (use our Dictionary!)
- Use words in sentences
- Create word associations

**Find Zambian novels and English textbooks in our library!**"""

    # Science
    elif 'science' in q or 'biology' in q or 'chemistry' in q or 'physics' in q:
        return """🔬 **Science Study Guide**

**Biology Topics:**
- Cells and tissues
- Human body systems
- Plants and photosynthesis
- Ecology and environment

**Chemistry Topics:**
- Elements and compounds
- Chemical reactions
- Acids and bases
- Periodic table

**Physics Topics:**
- Motion and forces
- Energy and electricity
- Light and sound
- Magnetism

**Study Tips:**
✅ Draw diagrams to understand concepts
✅ Conduct simple experiments at home
✅ Use our library for Science textbooks
✅ Practice with past papers
✅ Explain concepts to friends

**Available in library:**
- ECZ Science past papers
- Illustrated guides
- Practice questions

Which science subject needs the most help?"""

    # Zambia/Geography
    elif 'zambia' in q or 'province' in q:
        return """🇿🇲 **Zambia Facts**

**10 Provinces:**
1. Lusaka (Capital)
2. Copperbelt
3. Southern (Victoria Falls)
4. Central
5. Eastern
6. Western
7. Northern
8. North-Western
9. Luapula
10. Muchinga

**Key Facts:**
- 🌍 Area: 752,612 km²
- 👥 Population: ~19 million
- 💰 Currency: Zambian Kwacha (K)
- 🗣️ Official language: English
- 🏞️ Famous for: Victoria Falls (Mosi-oa-Tunya)

**National Anthem:** "Stand and Sing of Zambia, Proud and Free"

**Learn more about Zambian culture in our Zambian Novels section!**"""

    # Books/Library
    elif 'book' in q or 'library' in q or 'read' in q:
        return """📚 **Bantu Books Zambia Library**

**What We Offer:**

📝 **ECZ Exam Papers**
- Grade 7, 9, 12 past papers
- Marking schemes
- Subject-specific materials

🎓 **University Materials**
- Lecture notes
- Textbooks
- Research papers

📖 **Zambian Novels**
- Classic literature
- Contemporary fiction
- Short stories

👶 **Children Books**
- Early readers (ages 3-6)
- Middle readers (ages 7-10)
- Young adults (ages 11-14)

💼 **Professional Development**
- Business resources
- Teaching materials
- Technical skills

**How to access:**
1. Search by title, author, or category
2. Filter by grade level
3. Download or read online
4. Save to your library

**Start exploring today!** 🔍"""

    # Dictionary/Words
    elif 'word' in q or 'define' in q or 'meaning' in q:
        return """📖 **Dictionary Help**

**Did you know?**
We have a full dictionary feature! 

**To look up a word:**
1. Visit our Dictionary section
2. Search for any word
3. See definition, examples, synonyms
4. Save words to your history

**Features:**
- 🔤 A-Z word browsing
- 📝 Example sentences
- 🔗 Synonyms and antonyms
- 🇿🇲 Zambian terms
- 🔊 Audio pronunciations (coming soon)

**Try our Dictionary today!**

Is there a specific word you'd like to know about?"""

    # General greeting
    elif any(word in q for word in ['hi', 'hello', 'hey', 'greetings']):
        greetings = [
            """👋 Hello! I'm Bantu AI, your study assistant!

I can help you with:
- 📚 ECZ exam preparation
- ✏️ Study techniques
- 📖 Book recommendations
- 🔤 Word definitions
- 🇿🇲 Zambian education

What would you like to learn today?""",
            
            """Hi there! 👋 Welcome to Bantu Books Zambia!

I'm here to help you succeed in your studies. 

**Quick tips:**
- Need exam papers? Check ECZ category
- Want to learn new words? Visit Dictionary
- Looking for novels? Browse Zambian Novels

How can I assist you today? 📚"""
        ]
        return random.choice(greetings)
    
    # Default response
    else:
        responses = [
            f"""Thank you for your question! 

I understand you're asking about: "{question[:100]}..."

I can help with:
📚 **ECZ exam preparation** - Past papers, study guides
✏️ **Study techniques** - Active recall, spaced repetition
📖 **Book recommendations** - Find the right book for you
🔤 **Word definitions** - Use our Dictionary feature
🇿🇲 **Zambian education** - Curriculum, subjects, exams

Could you please be more specific about what you'd like to know?

For example:
- "How to prepare for ECZ Grade 12 Math?"
- "What are good study techniques?"
- "Recommend a Zambian novel" 🎯""",
            
            f"""Thanks for your message! 

To give you the best help, could you tell me more about what you're looking for?

**Quick links to helpful resources:**
🔍 **Dictionary** - Look up word meanings
📚 **Library** - Browse our book collection
📝 **ECZ Papers** - Practice past exams
🎓 **Study Tips** - Improve your learning

Your question: "{question[:100]}..."

Let me know how I can help specifically! 💡"""
        ]
        return random.choice(responses)


def get_suggestions(request):
    """Get suggested questions for AI"""
    suggestions = [
        "How can I prepare for ECZ Grade 12 exams?",
        "What are the best study techniques for students?",
        "Explain the Zambian education system",
        "How to improve my English vocabulary?",
        "Tips for passing Mathematics exam",
        "What books should I read for literature class?",
        "How to create an effective study schedule?",
        "Tell me about Zambia's 10 provinces",
        "How to prepare for Science practical exams?",
        "Recommend a Zambian novel for beginners"
    ]
    return JsonResponse({'suggestions': suggestions})


def clear_usage(request):
    """Clear usage counter (for testing)"""
    if request.user.is_staff:
        for key in list(request.session.keys()):
            if key.startswith('ai_usage_'):
                del request.session[key]
        return JsonResponse({'success': True, 'message': 'Usage cleared'})
    return JsonResponse({'error': 'Unauthorized'}, status=403)