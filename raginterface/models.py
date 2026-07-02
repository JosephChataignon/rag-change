from django.db import models



class ChatLog(models.Model):
    session_key = models.CharField(max_length=40, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.JSONField(default=dict)
    summary = models.TextField(default="")

    def __str__(self):
        summary = self.summary if (self.summary and self.summary != '') else str(self.content)
        return f"[{self.created_at}] chat {self.id} - {summary[:50]}..."
