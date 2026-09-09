# Setup and Usage

[← Back to Home](Home.md)

This page is derived from the repository's `README.md`, with added detail on prerequisites and what to expect.

## Prerequisites

- Python compatible with Django 1.8 (Python 2.7 or Python 3.3/3.4-era — Django 1.8 is the last Django release with Python 2.6 support and one of the first with Python 3 support; use whichever interpreter your environment already has configured for this project).
- `pip`, to install dependencies from `requirements.txt`.

## 1. Install dependencies

```
pip install -r requirements.txt
```

This installs `Django>=1.8,<1.9` — the only pinned dependency (see `requirements.txt`). No other third-party packages (no DRF, no `django-crispy-forms`, no `psycopg2`, etc.) are required.

## 2. Create the database tables

The project uses SQLite by default (`apps/settings.py` → `DATABASES['default']`, file `db.sqlite3` at the repository root). Apply migrations with:

```
./manage.py migrate
```

⚠️ **Known issue**: if the `db.sqlite3` file already contains `Gift` rows from a prior `0001_initial` state, running the `0002_auto_20170730_2249` migration will fail with `NameError: name 'book' is not defined`, because of a bug in its data-migration function. See [Known Issues](Known-Issues.md#migration-namerror-book-is-not-defined) for the fix needed before this will succeed on non-empty data. On a **fresh** database (no `Gift` rows yet), the migration's `RunPython` step iterates zero rows and succeeds trivially.

## 3. Run the development server

```
./manage.py runserver
```

By default this serves at <http://localhost:8000/>.

## 4. Create an admin (superuser) account

```
./manage.py createsuperuser
```

Follow the interactive prompts for username/email/password.

## 5. Log in to the admin site

Visit <http://localhost:8000/admin/> and log in with the superuser credentials created above. From there you can:

- Create/edit/delete `Registry` objects (each optionally linked to a `User`).
- Create/edit/delete `Gift` objects (name, price, registry, `bought_by`, `bought_by_list`, `fulfilled`, `amount_paid`) — since both models are registered with the plain default `ModelAdmin` (`gifts/admin.py`), all fields are editable via the auto-generated admin form.

## 6. Create ordinary (non-superuser) accounts

Per the README: to create a normal (non-superuser) user, log into `/admin/` as a superuser and create the user from there (there is no public self-service signup page in this app).

## Using the application

- Visiting `/` shows a static HTML snippet from `apps.views.home` with stale demo links; see [Known Issues](Known-Issues.md#stale-links-on-the-home-page) — none of those links go anywhere useful.
- Visiting `/gifts/` is intended to show a bulleted list of all gift names, but currently raises a server error due to a bug in `GiftListView.get_context_data`; see [Known Issues](Known-Issues.md#giftlistview-namerror-articlelistview-is-not-defined) for the one-line fix.
- There is currently no UI flow to create a registry, add a gift, or buy/pay for a gift as an end user — those actions can only be performed today through the Django admin (`/admin/`), or programmatically via the Django shell using the helper functions/models directly (see [Views and Routes](Views-and-Routes.md#unused-helper-functions-giftsviewspy)).

## Quick reference

| Command                     | Purpose                                    |
|-------------------------------|---------------------------------------------|
| `pip install -r requirements.txt` | Install Django 1.8.x                    |
| `./manage.py migrate`         | Create/update database schema                |
| `./manage.py runserver`       | Start the dev server at `localhost:8000`     |
| `./manage.py createsuperuser` | Create an admin account                      |
| `./manage.py test`            | Run the (currently empty) test suite — see [Testing](Testing.md) |
