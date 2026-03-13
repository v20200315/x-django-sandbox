# Recreated to match DB state: original 0001 created UDI.
# 0002 will replace UDI with DI.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UDI',
            fields=[
                (
                    'id',
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ('di', models.CharField(help_text='Device Identifier', max_length=255)),
                (
                    'pi',
                    models.CharField(
                        blank=True, help_text='Production Identifier', max_length=255
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'owner',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='udi_records',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'UDI',
                'verbose_name_plural': 'UDIs',
                'ordering': ['-created_at'],
            },
        ),
    ]
