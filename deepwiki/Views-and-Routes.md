# Views and Routes

[← Back to Home](Home.md)

## URL → View → Template table

| URL pattern         | Defined in            | View                                          | Template                          | Notes |
|----------------------|------------------------|-------------------------------------------------|-------------------------------------|-------|
| `/admin/`             | `apps/urls.py:9`       | `django.contrib.admin.site.urls`                | Django admin's own templates        | Standard Django admin, `Gift` and `Registry` registered (see below). |
| `/gifts/`             | `apps/urls.py:10` → `gifts/urls.py:6` | `gifts.views.GiftListView` (name `gifts-list`, namespace `gifts`) | `gifts/templates/gifts_list.html` | Public, lists **all** `Gift` rows, no filtering by registry/user. |
| `/`                   | `apps/urls.py:11`       | `apps.views.home`                                | none (raw `HttpResponse`)          | Legacy landing page with stale links (see [Known Issues](Known-Issues.md)). |

The full name for the gifts list route, when reversed with Django's `{% url %}` tag or `reverse()`, is `gifts:gifts-list` (because of the `namespace='gifts'` on the `include()` in `apps/urls.py`).

## `apps.views.home` (`apps/views.py`)

```python
def home(request):
    html = """
    <h1>Django CRUD Example</h1>
    <a href="/books_cbv/">Class Based Views</a><br>
    <a href="/books_fbv/">Function Based Views</a><br>    
    <a href="/books_fbv_user/">Function Based Views with User Access</a><br>    
    """
    return HttpResponse(html)
```

This is a leftover from a generic Django tutorial/boilerplate ("Django CRUD Example" with Books). It:

- Returns a raw HTML string via `HttpResponse` rather than rendering a template.
- Links to `/books_cbv/`, `/books_fbv/`, and `/books_fbv_user/`, none of which exist anywhere in `apps/urls.py` or `gifts/urls.py`. Following any of these links returns Django's 404 page. See [Known Issues](Known-Issues.md#stale-links-on-the-home-page).
- Has unused imports (`render`, `redirect`, `get_object_or_404` are imported but never used in this file).

## `gifts.views.GiftListView` (`gifts/views.py`)

```python
class GiftListView(ListView):

    model = Gift

    def get_context_data(self, **kwargs):
        context = super(ArticleListView, self).get_context_data(**kwargs)
        return context
```

- A standard Django `ListView` bound to the `Gift` model; by default this queries `Gift.objects.all()` and renders it as `object_list` (and `gift_list`) in the template context.
- The `get_context_data` override is a no-op **if it worked** — it just calls `super()` and returns the context unchanged — but it **cannot** currently work, because it references `ArticleListView`, a class that is never imported or defined anywhere in this codebase. Any request to `/gifts/` triggers this method and raises `NameError: name 'ArticleListView' is not defined`, so **`/gifts/` currently returns HTTP 500 for every request.** See [Known Issues](Known-Issues.md#giftlistview-namerror-articlelistview-is-not-defined).
- `timezone` and `Registry` are imported in this module but not used within `GiftListView` itself.

### Template: `gifts/templates/gifts_list.html`

```html
<h1>Gifts</h1>
<ul>
{% for gift in object_list %}
    <li>{{ gift.name }}</li>
{% empty %}
    <li>No gifts yet.</li>
{% endfor %}
</ul>
```

Iterates `object_list` (the default context variable name Django's `ListView` provides) and prints each gift's `name`. No price, fulfilled state, or buyer information is shown — if `get_context_data` were fixed, the view would still only ever render the gift's name.

## Unused helper functions (`gifts/views.py`)

These four module-level functions are defined but **not referenced by any URL, view, template, or test** in the repository. They read as a sketch of the intended registry/gift/purchase workflow that was never finished being wired up:

### `create_registry(user, context)`

```python
def create_registry(user, context):
    context['registry'], created = Registry.objects.get_or_create(user=user)
    return context
```

Gets or creates a `Registry` for `user` and stashes it (plus a `created` boolean, which is silently discarded — only `context['registry']` is set) into a caller-supplied `context` dict. Callers must pass in a pre-existing `context` dict; the function does not create one.

### `register_gift(registry, name, price)`

```python
def register_gift(registry, name, price):
    context['gift'], created = Gift.objects.get_or_create(registry=registry, name=name, price=price)
    return context
```

Intended to get-or-create a `Gift` on a `registry`. **This function references `context`, which is never defined or passed in as a parameter** — calling it raises `NameError: name 'context' is not defined`. This is a third bug beyond the two called out in the implementation plan; see [Known Issues](Known-Issues.md).

### `get_unfulfilled_gifts(registry)`

```python
def get_unfulfilled_gifts(registry):
    context['unfulfilled_gifts'] = Gift.objects.filter(registry=registry, fulfilled=False)
    return context
```

Same issue as `register_gift` — `context` is referenced but never defined inside the function or passed as a parameter, so calling it also raises `NameError`.

### `buy_gift(user, gift, amount_paid=None)`

```python
def buy_gift(user, gift, amount_paid=None):
    gift.bought_by_list.add(user)
    if amount_paid:
        gift.amount_paid += amount_paid
        if gift.amount_paid >= gift.price:
            gift.fulfilled = True
    else:
        gift.fulfilled = True
    gift.save()
```

This is the one helper that is internally self-consistent (no undefined names) and would work if called directly with a real `User` and `Gift` instance:

- Adds `user` to `gift.bought_by_list` unconditionally.
- If `amount_paid` is given and truthy, adds it to the running `gift.amount_paid` total and marks `fulfilled = True` once the cumulative amount reaches or exceeds `price`.
- If `amount_paid` is falsy/omitted, marks the gift `fulfilled = True` immediately (treated as "someone bought the whole gift").
- Saves the `Gift`.

Caveats: no validators run on plain `.save()` (see [Data Model](Data-Model.md#notes-on-validation)), so `amount_paid` could exceed `price` without error, and there's no guard against calling this twice for the same user (they'd just be added to the M2M again, which is a no-op, but `amount_paid` would double-increment).

## Candidates for future wiring

If this app is developed further, these helpers are natural building blocks for real views/URLs, e.g.:

- `create_registry` → a "my registry" view for logged-in users.
- `register_gift` → a form view to add a gift to the current user's registry (needs the `context` bug fixed first).
- `get_unfulfilled_gifts` → filtering support for `GiftListView` (needs the `context` bug fixed first).
- `buy_gift` → a POST endpoint for "mark as bought" / "contribute payment" actions on a gift detail page.

None of this exists yet; see [Known Issues](Known-Issues.md) for the concrete bugs blocking `GiftListView` and the migration, and [Testing](Testing.md) for suggested coverage once these are wired up.
