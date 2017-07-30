from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class Registry(models.Model):
    user = models.OneToOneField(User, blank=True, null=True, on_delete=models.SET_NULL)

class Gift(models.Model):
    registry = models.ForeignKey(Registry, blank=True, null=True, on_delete=models.SET_NULL)

    name = models.CharField(max_length=200, blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.0)])

    bought_by = models.OneToOneField(User, blank=True, null=True, on_delete=models.SET_NULL)
    bought_by_list = models.ManyToManyField(User, blank=True, null=True, related_name='+')
    fulfilled = models.BooleanField(default=False)

    amount_paid = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.0)], default=0.0)
