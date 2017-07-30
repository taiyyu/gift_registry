from django.shortcuts import render

# Create your views here.
from django.views.generic.list import ListView
from django.utils import timezone

from gifts.models import Gift, Registry

class GiftListView(ListView):

    model = Gift

    def get_context_data(self, **kwargs):
        context = super(ArticleListView, self).get_context_data(**kwargs)
        return context

def create_registry(user, context):
    context['registry'], created = Registry.objects.get_or_create(user=user)
    return context

# the user experience flow is...
def register_gift(registry, name, price):
    context['gift'], created = Gift.objects.get_or_create(registry=registry, name=name, price=price)
    return context

def get_unfulfilled_gifts(registry):
    context['unfulfilled_gifts'] = Gift.objects.filter(registry=registry, fulfilled=False)
    return context

def buy_gift(user, gift, amount_paid=None):
    gift.bought_by_list.add(user)
    if amount_paid:
        gift.amount_paid += amount_paid
        if gift.amount_paid >= gift.price:
            gift.fulfilled = True
    else:
        gift.fulfilled = True
    gift.save()
