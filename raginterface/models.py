from django.db import models



class ChatLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.JSONField(default=dict)
    summary = models.TextField(default="")

    def __str__(self):
        summary = self.summary if (self.summary and self.summary != '') else str(self.content)
        return f"[{self.timestamp}] chat {self.id} - {summary[:50]}..."
