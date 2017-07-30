# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.core.validators

def make_many_bought_by_list(apps, schema_editor):
    """
        Adds the Author object in Book.author to the
        many-to-many relationship in Book.authors
    """
    Gift = apps.get_model('gifts', 'Gift')

    for gift in Gift.objects.all():
        gift.bought_by_list.add(book.bought_by)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gifts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gift',
            name='amount_paid',
            field=models.DecimalField(default=0.0, max_digits=6, decimal_places=2, validators=[django.core.validators.MinValueValidator(0.0)]),
        ),
        migrations.AddField(
            model_name='gift',
            name='bought_by_list',
            field=models.ManyToManyField(related_name='_gift_bought_by_list_+', null=True, to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.RunPython(make_many_bought_by_list),
    ]
