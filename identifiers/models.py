import uuid

from django.db import models


class AI(models.Model):
    """
    AI (Application Identifier) - base/reference data.
    PI in UDI-DI-PI is composed of multiple AIs.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True, help_text='AI code (e.g. 01, 17)')
    description = models.CharField(max_length=255, blank=True)
    format_spec = models.CharField(
        max_length=50, blank=True,
        help_text='Format spec (e.g. N14, an..20)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Application Identifier'
        verbose_name_plural = 'Application Identifiers'

    def __str__(self):
        return f'{self.code} - {self.description or "(no description)"}'


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


class UDIDIPI(models.Model):
    """
    UDI-DI-PI record. Generated from selected DIs and AI values per GS1 rules.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='udidipi_records',
    )
    generated_code = models.CharField(
        max_length=500,
        help_text='Generated UDI-DI-PI code per GS1 rules',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    dis = models.ManyToManyField(
        DI,
        through='UDIDIPIDILink',
        related_name='udidipi_records',
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'UDI-DI-PI'
        verbose_name_plural = 'UDI-DI-PIs'

    def __str__(self):
        return self.generated_code[:50] + ('...' if len(self.generated_code) > 50 else '')


class UDIDIPIDILink(models.Model):
    """Links UDIDIPI to DIs with ordering."""

    udidipi = models.ForeignKey(UDIDIPI, on_delete=models.CASCADE)
    di = models.ForeignKey(DI, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = [('udidipi', 'di')]


class UDIDIPIAIValue(models.Model):
    """AI value for a UDIDIPI record."""

    udidipi = models.ForeignKey(UDIDIPI, on_delete=models.CASCADE)
    ai = models.ForeignKey(AI, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = [('udidipi', 'ai')]

    def __str__(self):
        return f'{self.ai.code}={self.value}'
