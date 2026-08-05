from django.db import models


class ProcessedMessage(models.Model):
    event_id = models.CharField(max_length=100, unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-processed_at']

    def __str__(self) -> 'str':
        return self.event_id
