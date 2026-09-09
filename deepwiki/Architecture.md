# Architecture

[← Back to Home](Home.md)

## Two-app split

Django separates the *project* (global configuration) from *apps* (installable, reusable features). In this repo:

- **`apps/`** — the Django **project** package, created by `django-admin startproject apps`. It holds:
  - `apps/settings.py` — global settings (installed apps, middleware, database, templates, `LOGIN_URL`).
  - `apps/urls.py` — the root URLconf, pointed to by `ROOT_URLCONF = 'apps.urls'`.
  - `apps/views.py` — a single legacy view, `home`, wired to `/`.
  - `apps/wsgi.py` — the WSGI entry point (`apps.wsgi.application`), used by `manage.py runserver` and any production WSGI server.

- **`gifts/`** — the single installed Django **app** (registered in `INSTALLED_APPS` in `apps/settings.py`), implementing the actual gift-registry feature:
  - `gifts/models.py` — `Registry` and `Gift` models ([Data Model](Data-Model.md)).
  - `gifts/views.py` — `GiftListView` plus several unused helper functions ([Views and Routes](Views-and-Routes.md)).
  - `gifts/urls.py` — the app's own URLconf, included into the root URLconf under the `gifts` namespace.
  - `gifts/admin.py` — registers `Gift` and `Registry` with the default admin `ModelAdmin`.
  - `gifts/migrations/` — schema history ([Data Model](Data-Model.md#migration-history)).
  - `gifts/templates/gifts_list.html` — the only template in the project.
  - `gifts/tests.py` — an empty stub ([Testing](Testing.md)).

There is no second feature app despite the project-level package being named `apps` (plural) — this name is simply the leftover default from `startproject`.

## Request flow

For every incoming HTTP request, Django resolves the URL against `ROOT_URLCONF = 'apps.urls'`:

```
apps/urls.py
├── ^admin/   → django.contrib.admin.site.urls   (Django's built-in admin)
├── ^gifts/   → include('gifts.urls', namespace='gifts')
│                 └── ^$ → gifts.views.GiftListView.as_view()   name='gifts-list'
└── ^$        → apps.views.home
```

- `GET /` → `apps.views.home` → returns a raw `HttpResponse` containing a small HTML snippet (**not** a rendered template). The links inside it are stale — see [Known Issues](Known-Issues.md).
- `GET /gifts/` → `gifts.views.GiftListView` (a Django `ListView` over the `Gift` model) → renders `gifts/templates/gifts_list.html`, which by Django's default `ListView` template-resolution convention is looked up as `gifts_list.html` because `GiftListView` does not set `template_name` explicitly and the template happens to live at the top level of `gifts/templates/` (not under a `gifts/` subdirectory, which is the more common convention). It works here because `APP_DIRS = True` and the file is directly discoverable under `templates/`.
- `GET /admin/` → Django's built-in admin site, which lists the registered `Gift` and `Registry` models (see [Data Model](Data-Model.md)).

There is no authentication check, permission check, or login-required decorator anywhere in `gifts/views.py` — `GiftListView` is fully public and lists **every** `Gift` in the database, not just those belonging to the requesting user's registry.

## Settings highlights (`apps/settings.py`)

- `DEBUG = True` and a hard-coded `SECRET_KEY` — fine for local development, not safe for production use as-is.
- `INSTALLED_APPS` is a **tuple** (Django-1.8 convention) containing the standard `django.contrib.*` apps plus `gifts`.
- `MIDDLEWARE_CLASSES` (not `MIDDLEWARE`) is a **tuple** of middleware paths — this is the Django ≤1.9 setting name; it was replaced by the list-based `MIDDLEWARE` setting in Django 1.10.
- `ROOT_URLCONF = 'apps.urls'`.
- `TEMPLATES` uses the modern (Django 1.8+) `TEMPLATES` list-of-backends format, with `APP_DIRS = True` so each app's `templates/` directory is searched automatically.
- `DATABASES['default']` is SQLite, stored at `<BASE_DIR>/db.sqlite3`.
- `LOGIN_URL = '/admin/login/'` — this is set, but nothing in `gifts` actually enforces login (no `@login_required` view, no `LoginRequiredMixin` on `GiftListView`), so it currently has no observable effect on the gifts app itself.
- `WSGI_APPLICATION = 'apps.wsgi.application'`.

## Data flow summary

```
Browser ── HTTP ──▶ apps/urls.py ──▶ gifts/urls.py ──▶ gifts/views.py (GiftListView)
                                                              │
                                                              ▼
                                                     gifts/models.py (Gift, Registry)
                                                              │
                                                              ▼
                                                        db.sqlite3 (via ORM)
                                                              │
                                                              ▼
                                            gifts/templates/gifts_list.html ──▶ HttpResponse
```

See [Data Model](Data-Model.md) for the schema and [Views and Routes](Views-and-Routes.md) for full view-level detail.
