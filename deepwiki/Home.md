# Gift Registry — DeepWiki

This is a DeepWiki-style, hand-curated documentation set for the `gift_registry` repository. It was produced by manually inspecting the source tree (no `ai-codex`/`deepwiki` skill matching the requested name was available in `gh skill search`, see [Known Issues](Known-Issues.md#tooling-note) for details) and following the standard DeepWiki page structure.

## What is this project?

`gift_registry` is a small, server-rendered Django application that lets a user create a **gift registry** and add **gifts** (name + price) to it. Other users can then mark a gift as bought, or make a partial payment toward its price, so the registry owner knows what's still needed. It is built on **Django 1.8** and uses **SQLite** for storage. There is no REST API, no JavaScript framework, and no CSS framework — just Django's built-in template engine and the default admin site.

## Pages

- [Overview](Overview.md) — what the app does, tech stack, repo layout.
- [Architecture](Architecture.md) — the two-app split, request flow, settings highlights.
- [Data Model](Data-Model.md) — `Registry` / `Gift` models, relationships, migration history.
- [Views and Routes](Views-and-Routes.md) — URL → view → template mapping, unused helper functions.
- [Setup and Usage](Setup-and-Usage.md) — install, migrate, run, create a superuser, use the admin.
- [Testing](Testing.md) — current (lack of) test coverage and suggested targets.
- [Known Issues](Known-Issues.md) — the bugs and stale code found while writing this wiki.

## Repository layout

```
gift_registry/
├── README.md                # Original project README
├── requirements.txt         # Django>=1.8,<1.9
├── manage.py                # Django management entry point
├── db.sqlite3                # Default SQLite database file
├── apps/                     # Django *project* package (settings/urls/wsgi)
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   └── wsgi.py
└── gifts/                    # Django *feature* app
    ├── __init__.py
    ├── apps.py
    ├── admin.py
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── tests.py
    ├── migrations/
    │   ├── __init__.py
    │   ├── 0001_initial.py
    │   └── 0002_auto_20170730_2249.py
    └── templates/
        └── gifts_list.html
```

Note the naming: the top-level Django *project* is confusingly called `apps` (this is the directory created by `django-admin startproject apps`), while the single installed Django *app* that implements the actual feature is `gifts`. See [Architecture](Architecture.md) for more on this split.
