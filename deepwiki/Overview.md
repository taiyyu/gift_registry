# Overview

[← Back to Home](Home.md)

## Purpose

`gift_registry` is a minimal gift-registry web application:

1. A user has a `Registry` (one per `User`, via `gifts/models.py`).
2. The registry contains `Gift` items — each with a `name` and a `price`.
3. Other people ("gifters") can mark a gift as bought, or contribute a partial payment (`amount_paid`) toward its price, until the gift is `fulfilled`.

The intended user flow, as suggested by the (currently unused) helper functions in `gifts/views.py`, would be:

- `create_registry(user, context)` — get-or-create a `Registry` for a user.
- `register_gift(registry, name, price)` — get-or-create a `Gift` on that registry.
- `get_unfulfilled_gifts(registry)` — list gifts still needing to be bought.
- `buy_gift(user, gift, amount_paid=None)` — record that `user` bought/contributed to `gift`, marking it `fulfilled` once fully paid (or immediately, if no `amount_paid` is given, i.e. a straight "I bought this" action).

**None of these helper functions are currently wired to a URL, view, or template.** The only thing actually reachable through the browser today is a bare list of gift names at `/gifts/`. See [Views and Routes](Views-and-Routes.md) for the full picture and [Known Issues](Known-Issues.md) for the bugs that would need fixing before these flows work end-to-end.

## Tech stack

| Layer            | Technology                                             |
|-------------------|--------------------------------------------------------|
| Language          | Python 2/3 compatible (`from __future__ import unicode_literals` throughout) |
| Web framework     | Django `>=1.8,<1.9` (see `requirements.txt`)            |
| Database          | SQLite (`db.sqlite3`, via `django.db.backends.sqlite3`) |
| API layer         | None — no Django REST Framework, no JSON API            |
| Frontend          | None — server-rendered Django templates only, no CSS/JS framework, no build step |
| Admin             | Django's built-in `django.contrib.admin`, with `Gift` and `Registry` registered using the default `ModelAdmin` |
| Auth              | Django's built-in `django.contrib.auth` (`User` model); `LOGIN_URL` points at `/admin/login/` |

Django 1.8 predates several conventions that later became standard in Django, and the codebase reflects that:

- `gifts/urls.py` uses the legacy `django.conf.urls.patterns()` helper (removed in Django 1.10+), not the modern list-of-`url()` style used elsewhere.
- `apps/settings.py` uses the tuple-based `MIDDLEWARE_CLASSES` setting (renamed to the list-based `MIDDLEWARE` starting in Django 1.10), referencing middleware classes that have since been renamed or removed in newer Django (e.g. `SessionAuthenticationMiddleware` was removed in Django 2.0).

This wiki intentionally describes these as Django-1.8-era APIs rather than "modernizing" them in the text, since the actual code has not been changed as part of this task.

## Repository layout diagram

See [Home](Home.md#repository-layout) for the full directory tree. In short: `apps/` is the Django project (settings/urls/wsgi), `gifts/` is the one and only installed app.
