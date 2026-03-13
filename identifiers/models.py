import uuid

from django.db import models


class DI(models.Model):
    """
    DI (Device Identifier) record.
    Each record belongs to the user who created it.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='di_records',
    )
    value = models.CharField(max_length=255, help_text='Device Identifier value')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'DI'
        verbose_name_plural = 'DIs'

    def __str__(self):
        return self.value
