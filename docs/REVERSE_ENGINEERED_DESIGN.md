# Gift Registry — Reverse-Engineered Design Document

Status: derived entirely from the code as committed at `602a3f7` ("Initial Version").
This document describes what is actually implemented, not what the project
aspires to be. Aspirational/unfinished pieces and outright bugs are called
out explicitly rather than smoothed over.

## 1. Purpose & Scope

Per `README.md`, this project implements a "Gift Registry": a place where a
user can register gifts they want, and other users can mark gifts as bought
(possibly splitting the cost across multiple buyers). The README explicitly
flags that a "v1 to v2" migration exists to move from a single-buyer model
(`bought_by`) to a multi-buyer model (`bought_by_list`), and that `bought_by`
"can be deprecated once refactored out completely" — i.e. the multi-buyer /
split-payment model is the intended long-term design, with the single-buyer
field kept around only for backward compatibility during the transition.

In its current state the repository is a **prototype / scaffold**: the data
model and one core business function (`buy_gift`) are correctly implemented,
but the web layer (views, URLs, templates, forms) needed to actually use the
registry/gift/buy workflow from a browser is missing or broken. The only
end-to-end working surfaces are the Django admin and a single, mostly empty
gift-listing page.

## 2. Tech Stack & Constraints

- **Framework:** Django, pinned in `requirements.txt` as `Django>=1.8,<1.9`.
- **Hard version ceiling:** the code uses APIs removed in Django 1.10+:
  - `django.conf.urls.patterns()` in `gifts/urls.py` (removed in 1.10).
  - String view references passed to `url()` (e.g. `url(r'^$', 'apps.views.home')`
    in `apps/urls.py`) — string-based view lookup was removed in 1.10.
  - `django.contrib.auth.middleware.SessionAuthenticationMiddleware` in
    `MIDDLEWARE_CLASSES` — removed in Django 2.1, and `MIDDLEWARE_CLASSES`
    itself (vs. `MIDDLEWARE`) is the pre-1.10 setting name.
  So despite the loose `<1.9` constraint the code will genuinely only run on
  the Django 1.8.x line as written.
- **Database:** SQLite (`db.sqlite3`), configured via `apps/settings.py`,
  file checked directly into the repo (see §7, known defects).
- **Frontend:** none — server-rendered Django templates only, and only one
  trivial template exists (`gifts/templates/gifts_list.html`).
- **Python:** implied Python 2.7 / early Python 3 era, consistent with
  Django 1.8's own supported interpreters; there's no explicit interpreter
  pin in the repo.
- **Auth:** relies entirely on `django.contrib.auth` (the built-in `User`
  model) and the Django admin for account management. The README explicitly
  states normal (non-superuser) accounts must be created by an admin through
  `/admin/`, since there is no registration view.

## 3. Architecture (textual diagram)

```
apps/                         <- Django "project" (site-wide config)
  settings.py                 <- INSTALLED_APPS = [django.contrib.*, "gifts"]
  urls.py                     <- root URLconf: /admin/, /gifts/, /
  views.py                    <- home() — dead tutorial boilerplate, unrelated to gifts
  wsgi.py                     <- WSGI entrypoint

gifts/                        <- the one feature app, "Gift Registry" domain
  models.py                   <- Registry, Gift
  admin.py                    <- ModelAdmin registration for both models
  views.py                    <- GiftListView (broken) + free-function workflow (broken/partial)
  urls.py                     <- single route -> GiftListView
  templates/gifts_list.html   <- bare <ul> of gift names
  migrations/
    0001_initial.py           <- v1 schema: Registry, Gift(bought_by, fulfilled, price, name)
    0002_auto_20170730_2249.py <- v2 schema: + amount_paid, bought_by_list, data backfill (broken)
  tests.py                    <- empty
```

There is exactly one Django app (`gifts`) inside one Django project
(`apps`). The project layer contributes almost nothing to the gift-registry
feature itself — its `home` view is leftover boilerplate from an unrelated
Django CRUD tutorial (see §4).

## 4. Data Model / ER Description

```
User (django.contrib.auth.models.User)
  │
  │ 1                                  1
  ├──────────────< Registry >──────────┤  (Registry.user: OneToOne, SET_NULL, nullable)
  │                    │ 1
  │                    │
  │                    │ N
  │              Gift.registry (FK, SET_NULL, nullable)
  │                    │
  │                    ▼
  │                  Gift
  │                    │
  │  legacy, 1:1        \  current, N:M
  ├── Gift.bought_by ────┴── Gift.bought_by_list ──> User (M2M, related_name="+")
       (OneToOne, SET_NULL, nullable, deprecated)
```

- **Registry**
  - `user`: `OneToOneField(User, blank=True, null=True, on_delete=SET_NULL)`
    — at most one Registry per User. Because the FK is nullable and
    `SET_NULL`, a Registry row can outlive its owning User (becomes an
    "orphaned" registry with `user=None`) rather than being deleted with it.
- **Gift**
  - `registry`: `ForeignKey(Registry, blank=True, null=True, on_delete=SET_NULL)`
    — many gifts per registry; deleting a Registry does **not** delete its
    gifts, it nulls out `registry` on them (orphaned gifts).
  - `name`: `CharField(max_length=200, blank=True, null=True)`.
  - `price`: `DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.0)])`
    — required, non-negative, up to 9999.99.
  - `bought_by`: `OneToOneField(User, blank=True, null=True, on_delete=SET_NULL)`
    — **legacy** single-buyer field from schema v1.
  - `bought_by_list`: `ManyToManyField(User, blank=True, related_name="+")`
    — **current** multi-buyer field from schema v2; enables several users to
    split the cost of one gift. (Model declares `null=True` on the M2M as
    well, which Django silently ignores — M2M fields have no database
    column to be nullable, so this is a harmless no-op, not a functional bug.)
  - `fulfilled`: `BooleanField(default=False)` — whether the gift has been
    fully paid for / purchased.
  - `amount_paid`: `DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.0)], default=0.0)`
    — running total of contributions toward `price`, added in schema v2.

Per the README and the shape of `buy_gift()` (§6), the intended steady state
is: `bought_by` is deprecated/vestigial, and `bought_by_list` +
`amount_paid` + `fulfilled` together model "N people can each chip in
towards one gift; once the running total reaches the price, the gift is
fulfilled."

## 5. Schema Evolution: v1 → v2

- **`0001_initial.py` (v1):** creates `Registry` and `Gift` with only the
  single-buyer `bought_by` field. A gift is either bought (by exactly one
  user) or not; no partial payments.
- **`0002_auto_20170730_2249.py` (v2):** adds `amount_paid` and
  `bought_by_list`, then runs a `RunPython` data migration,
  `make_many_bought_by_list`, intended to backfill `bought_by_list` for every
  existing `Gift` from its old `bought_by` value — i.e. "every gift that had
  a single buyer under v1 should show that same buyer in the new list under
  v2."

  **This data migration is broken as written:**

  ```python
  def make_many_bought_by_list(apps, schema_editor):
      Gift = apps.get_model('gifts', 'Gift')
      for gift in Gift.objects.all():
          gift.bought_by_list.add(book.bought_by)   # <-- `book` is undefined
  ```

  The loop variable is `gift`, but the body references `book`, which does
  not exist anywhere in the migration or its imports. On any database that
  already contains at least one `Gift` row, running this migration raises
  `NameError: name 'book' is not defined` and the migration aborts (Django
  wraps `RunPython` in a transaction on backends that support it, so on
  SQLite the whole migration would roll back cleanly, but it still never
  completes). On a fresh, empty database the loop body never executes, so
  the bug is latent until real data exists — which is presumably how it
  shipped without being caught. The docstring inside the function ("Adds the
  Author object in Book.author ...") is also leftover copy-paste from a
  different (Book/Author) tutorial project, reinforcing that this migration
  was adapted from boilerplate rather than written from scratch for this
  model.

## 6. Request/Response Flow

### 6.1 Working today: `GET /gifts/`

1. `apps/urls.py` routes `^gifts/` to `include('gifts.urls', namespace='gifts')`.
2. `gifts/urls.py` routes the empty remaining path (`^$`) to
   `GiftListView.as_view()`, named `gifts-list`.
3. `GiftListView` is a plain Django `ListView` with `model = Gift` — Django's
   generic view machinery loads `Gift.objects.all()` and renders it against
   the app's default template resolution.
4. `GiftListView.get_context_data` (see below) is dead code that never
   executes on the happy path in a way that matters:
   ```python
   def get_context_data(self, **kwargs):
       context = super(ArticleListView, self).get_context_data(**kwargs)
       return context
   ```
   `ArticleListView` is never defined anywhere in the project (it's a
   copy-paste leftover — the correct name would be `GiftListView`). This
   method is a no-op even when it works (it does nothing beyond what
   `ListView` already does), but it is **not** a no-op in practice: because
   Django's generic `ListView` always calls `get_context_data()` when
   rendering, every single request to `/gifts/` raises
   `NameError: name 'ArticleListView' is not defined` and the page fails
   with a server error rather than actually rendering. In other words, this
   route is wired up correctly at the URL level but is currently broken at
   runtime; the plan's original assumption that this page "renders an empty
   list" is not accurate — it 500s.
5. Were it fixed, template resolution would find `gifts/templates/gifts_list.html`
   (Django's `APP_DIRS` template loader looks in each app's `templates/`
   directory) and render `{{ gift.name }}` for every `Gift`, or "No gifts
   yet." if there are none. Note the template lives at
   `gifts/templates/gifts_list.html`, not the conventional
   `gifts/templates/gifts/gifts_list.html`; because there is only one app
   with templates, there's no cross-app name collision today, but this
   flat layout is fragile if a second app is ever added.
6. There is no authentication check on this view — it is not scoped to
   "the current user's registry," it lists every `Gift` row in the database
   regardless of owner.

### 6.2 Broken/dead: `GET /`

`apps/urls.py` routes `^$` to `apps.views.home`, which returns a hardcoded
HTML fragment linking to `/books_cbv/`, `/books_fbv/`, and
`/books_fbv_user/`. None of these three paths are registered anywhere in
the project. This is leftover boilerplate from an unrelated Django
CRUD/tutorial exercise (the naming — "books", "CBV/FBV" — doesn't match the
gift-registry domain at all) and should be treated as dead code, not as a
partially-built gift-registry feature.

### 6.3 Intended but unbuilt: registry creation, gift registration, buying

`gifts/views.py` contains free functions that sketch the intended
end-user workflow, but none of them are:
- registered in `gifts/urls.py`,
- exposed as class-based or function-based *views* (they take domain
  objects like `user`/`registry`/`gift` as plain Python arguments, not an
  HTTP `request`),
- backed by any form or template.

So conceptually the intended flow is:

```
create_registry(user)        -> get-or-create the user's Registry
register_gift(registry, ...) -> get-or-create a Gift on that Registry
get_unfulfilled_gifts(registry) -> list gifts not yet fulfilled, e.g. for a "buy" page
buy_gift(user, gift, amount)  -> record a (partial) purchase
```

but as written this can only be exercised from the Django shell / a test,
never from a browser, and even then two of the four functions crash (see
§7).

## 7. Known Defects Inventory

1. **`context` is referenced but never defined** in `register_gift()` and
   `get_unfulfilled_gifts()` (`gifts/views.py`). Both functions accept
   only `(registry, name, price)` / `(registry)` respectively, with no
   `context` parameter, yet write to `context['gift']` / `context['unfulfilled_gifts']`.
   Calling either raises `NameError: name 'context' is not defined`. (By
   contrast, `create_registry(user, context)` *does* take `context` as a
   parameter and works correctly — the other two functions appear to have
   been copy-pasted from `create_registry` without updating the signature.)
2. **`ArticleListView` typo/undefined name** in `GiftListView.get_context_data`
   (`gifts/views.py`) — should be `GiftListView`. As explained in §6.1, this
   is not merely dead code: it is invoked on every request to `/gifts/` and
   currently 500s that page.
3. **Broken data migration** `make_many_bought_by_list` in
   `gifts/migrations/0002_auto_20170730_2249.py` references an undefined
   `book` variable instead of the loop variable `gift`. Fails with
   `NameError` on any database containing existing `Gift` rows; latent/silent
   on an empty database.
4. **Dead tutorial code in `apps/views.py:home`** — links to `/books_cbv/`,
   `/books_fbv/`, `/books_fbv_user/`, none of which exist, and none of which
   relate to gifts/registries.
5. **Use of Django APIs removed in 1.10+** — `django.conf.urls.patterns`
   (`gifts/urls.py`) and string-based view references in `url()`
   (`apps/urls.py`). This hard-pins the project to the Django 1.8.x line
   even though `requirements.txt` only asks for `<1.9`; there is no
   forward-compatible upgrade path without code changes.
6. **`SessionAuthenticationMiddleware`** in `MIDDLEWARE_CLASSES`
   (`apps/settings.py`) was removed in Django 2.1 and folded into
   `AuthenticationMiddleware`'s default behavior; another Django-1.8-only
   assumption baked into settings.
7. **Empty test suite** — `gifts/tests.py` contains only the
   `TestCase` import and a comment; there is zero automated coverage of the
   model validators, `buy_gift()`, or anything else.
8. **`db.sqlite3` is checked into version control** — a binary, mutable
   dev database sitting in the repo root. It will drift from migrations
   over time, bloats the git history with binary diffs, and risks
   accidentally shipping local/dev data. It is not `.gitignore`d.
9. **No forms/templates for the intended workflows** — there is no HTML
   form or template for creating a registry, registering a gift, or buying/
   splitting payment on a gift; the only functioning CRUD surface for these
   models is the Django admin (`gifts/admin.py`, default `ModelAdmin` for
   both `Gift` and `Registry` — functional but not designed for end users
   since it exposes every field and requires staff/admin login).
10. **No URL namespacing/authorization for "my registry"** — even once the
    `/gifts/` view is fixed, it lists *all* gifts globally rather than
    scoping to a logged-in user's own registry; there is no notion of "view
    someone else's registry by ID" either, so multi-user registries aren't
    actually browsable as separate entities today.

## 8. What Works End-to-End Today

- Django admin (`/admin/`) CRUD for `Gift` and `Registry`, once a superuser
  is created via `./manage.py createsuperuser` and (per the README) any
  additional non-superuser accounts are created by an admin through the
  same admin UI (there is no self-service signup).
- `Gift.objects` queries work correctly against the model as defined; the
  model layer itself (fields, validators, relations) has no bugs — all
  defects are in the migration/view layer built on top of it.
- `buy_gift(user, gift, amount_paid=None)` is the one fully correct piece of
  business logic in `gifts/views.py`: it adds `user` to `gift.bought_by_list`
  unconditionally; if `amount_paid` is supplied it accumulates it into
  `gift.amount_paid` and sets `fulfilled = True` once `amount_paid >= price`
  (supporting partial/split contributions across multiple calls/buyers); if
  no `amount_paid` is supplied it treats the call as a single full purchase
  and sets `fulfilled = True` immediately. It correctly `save()`s the gift
  in either branch. It is simply never called from any reachable code path.
- Everything else described as a "workflow" in this document is either
  broken (`/gifts/` 500s, the v2 data migration NameErrors on non-empty
  data) or entirely unreachable from the web (`create_registry`,
  `register_gift`, `get_unfulfilled_gifts`, `buy_gift`).

## 9. Recommendations for Anyone Picking This Up

1. **Fix `0002_auto_20170730_2249.py`** — change `book.bought_by` to
   `gift.bought_by`, and guard against `gift.bought_by is None` before
   calling `.add()` on the M2M (adding `None` to a M2M manager will raise).
   Since this is a data migration that already shipped in schema history,
   fixing it in place only helps repos that haven't run migrations yet;
   for a repo where `0002` has already been applied (successfully or not)
   in some environment, ship a follow-up data migration instead of editing
   history.
2. **Fix `GiftListView.get_context_data`** — replace `ArticleListView` with
   `GiftListView` (or simply delete the override, since it does nothing
   beyond calling `super()`).
3. **Fix the `context` `NameError`s** in `register_gift()` and
   `get_unfulfilled_gifts()` by adding a `context` parameter (matching
   `create_registry`'s signature) or, better, refactor away from mutating a
   shared `context` dict and have these functions simply `return` the
   registry/gift/queryset they compute, letting callers assemble their own
   template context.
4. **Turn the `gifts/views.py` free functions into real views** — wrap
   `create_registry`, `register_gift`, `get_unfulfilled_gifts`, and
   `buy_gift` in actual Django views (function- or class-based) bound to
   `request`/`request.user`, each with a corresponding entry in
   `gifts/urls.py`, a `ModelForm` (for gift name/price and for buy
   amount), and a template.
5. **Scope `/gifts/` (and any future registry page) to the logged-in user**
   — require login (`@login_required` / `LoginRequiredMixin`), and filter
   by the user's own `Registry` rather than listing every `Gift` globally;
   add a separate "view someone else's registry" route keyed by registry
   ID/slug for the actual gift-registry use case (buying gifts for someone
   else).
6. **Remove the dead tutorial code** in `apps/views.py:home` (the
   books_cbv/books_fbv links) and replace it with either a redirect to
   `/gifts/` or a minimal real landing page.
7. **Decide on a Django version and commit to it.** Either pin exactly to
   `Django==1.8.*` and keep the 1.8-only APIs (`patterns()`, string view
   refs, `SessionAuthenticationMiddleware`), or upgrade past 1.10+ and
   modernize `urls.py`/`settings.py` accordingly (`url()`/`re_path()` with
   view callables, `MIDDLEWARE` instead of `MIDDLEWARE_CLASSES`, drop
   `SessionAuthenticationMiddleware`). Also note Django 1.8 is long past
   EOL (April 2018); a real upgrade path off it entirely is worth
   considering for anything beyond a prototype.
8. **Add real tests** covering: model validators (negative price/amount
   rejected), `buy_gift()`'s partial/split-payment accumulation and
   `fulfilled` flag transition, the fixed data migration (via
   `django.test.migrations` / a migration test harness), and the view
   layer once it exists (registry creation, gift registration, buy flow,
   auth-gating).
9. **Stop tracking `db.sqlite3` in git.** Add it to `.gitignore`,
   `git rm --cached db.sqlite3`, and document `./manage.py migrate` as the
   way to get a local dev database (the README already documents this step
   — the checked-in file is redundant with it and only a liability).
10. **Deprecate `Gift.bought_by` for real** — once `bought_by_list` is the
    single source of truth and the backfill migration is fixed and applied,
    add a follow-up migration to drop the `bought_by` column, and remove
    any remaining references to it in code/admin.
