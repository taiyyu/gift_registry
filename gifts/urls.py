from django.conf.urls import patterns, url

from gifts.views import GiftListView

urlpatterns = patterns('',
  url(r'^$', GiftListView.as_view(), name='gifts-list'),
)
