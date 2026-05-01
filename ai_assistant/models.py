# ai_assistant/models.py
from django.db import models
from django.conf import settings

class AIUsage(models.Model):
    """Track AI assistant usage"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_usage')
    session_id = models.CharField(max_length=100, blank=True)
    question = models.TextField()
    answer = models.TextField()
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']
        verbose_name = "AI Usage"
        verbose_name_plural = "AI Usages"
    
    def __str__(self):
        return f"AI Query at {self.used_at}"