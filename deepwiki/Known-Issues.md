# Known Issues

[← Back to Home](Home.md)

This page documents bugs and stale code discovered while writing this wiki. **None of these are fixed as part of this documentation task** — they are called out here so future work has a clear, traceable starting point. Line numbers refer to the file contents at the time this wiki was written.

## `GiftListView` `NameError`: `ArticleListView` is not defined

**File:** `gifts/views.py`, lines 9–15

```python
class GiftListView(ListView):

    model = Gift

    def get_context_data(self, **kwargs):
        context = super(ArticleListView, self).get_context_data(**kwargs)
        return context
```

`get_context_data` calls `super(ArticleListView, self)`, but `ArticleListView` is never imported or defined anywhere in this codebase — it looks like leftover copy-paste from a different (Article-based) tutorial project. Because `ListView` always calls `get_context_data()` when rendering, **every request to `/gifts/` currently raises `NameError: name 'ArticleListView' is not defined` and returns HTTP 500** (or Django's debug traceback page, since `DEBUG = True`).

**Suggested fix:** change `super(ArticleListView, self)` to `super(GiftListView, self)` (or, since only Python 3 needs to be supported, simply `super().get_context_data(**kwargs)`).

Impact: **`/gifts/` is completely broken** in the current codebase — this is the single highest-impact bug in the repository, since it's the only user-facing feature route besides the admin.

## Migration `NameError`: `book` is not defined

**File:** `gifts/migrations/0002_auto_20170730_2249.py`, lines 8–16

```python
def make_many_bought_by_list(apps, schema_editor):
    """
        Adds the Author object in Book.author to the
        many-to-many relationship in Book.authors
    """
    Gift = apps.get_model('gifts', 'Gift')

    for gift in Gift.objects.all():
        gift.bought_by_list.add(book.bought_by)
```

The loop variable is `gift`, but the loop body references `book.bought_by` — `book` is never defined anywhere in this function (or module). This looks like it was adapted from an unrelated Django-tutorial migration for a `Book`/`Author` model (the docstring is a direct leftover from that source, referencing `Book.author`/`Book.authors`, which don't exist in this project at all).

Running `./manage.py migrate` against any database that already has one or more `Gift` rows in the `0001_initial` state will raise `NameError: name 'book' is not defined` during this migration and **abort partway through** (the two preceding `AddField` operations for `amount_paid` and `bought_by_list` will have already been applied, since `RunPython` is the last operation in the list — so the schema changes succeed but the data back-fill does not, leaving the migration marked as failed/unapplied depending on how Django's migration transaction handling behaves for the configured database backend).

On a **fresh** database with zero `Gift` rows, `Gift.objects.all()` is empty, the loop body never executes, and the migration succeeds — which is likely why this bug has gone unnoticed.

**Suggested fix:**

```python
for gift in Gift.objects.all():
    gift.bought_by_list.add(gift.bought_by)
```

...and update the docstring to describe what this migration actually does (back-filling `Gift.bought_by_list` from the legacy `Gift.bought_by` field), instead of the stale `Book`/`Author` description.

## `register_gift` and `get_unfulfilled_gifts` reference an undefined `context`

**File:** `gifts/views.py`

```python
def register_gift(registry, name, price):
    context['gift'], created = Gift.objects.get_or_create(registry=registry, name=name, price=price)
    return context

def get_unfulfilled_gifts(registry):
    context['unfulfilled_gifts'] = Gift.objects.filter(registry=registry, fulfilled=False)
    return context
```

Both functions read/write a module-level-looking `context` dict that is never defined inside the function body and never passed in as a parameter (contrast with `create_registry(user, context)`, which correctly takes `context` as an argument). Calling either function as written raises `NameError: name 'context' is not defined`.

Since neither function is currently called from anywhere in the codebase, this bug has no live impact today, but it will surface immediately the first time either helper is wired into a real view. **Suggested fix:** add a `context` parameter to both signatures, matching the pattern already used by `create_registry`.

## Stale links on the home page

**File:** `apps/views.py`

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

The `home` view (mapped to `/` in `apps/urls.py`) renders a static HTML snippet advertising a "Django CRUD Example" with links to `/books_cbv/`, `/books_fbv/`, and `/books_fbv_user/`. None of these routes are defined anywhere in `apps/urls.py` or `gifts/urls.py` — this content is leftover boilerplate from a generic Django tutorial and has nothing to do with the gift-registry feature. Visiting any of these links from `/` returns a plain Django 404. There is also no link from `/` to the actual feature, `/gifts/`.

Additionally, `apps/views.py` imports `render`, `redirect`, and `get_object_or_404`, none of which are used anywhere in the file.

**Suggested fix:** replace the placeholder HTML with a real landing page (ideally a rendered template rather than an inline `HttpResponse` string) that links to `/gifts/` and, once authentication-aware views exist, to registry-creation/login flows.

## No test coverage

`gifts/tests.py` is an empty stub, and there is no test file under `apps/` at all. See [Testing](Testing.md) for suggested coverage — notably, tests for `GiftListView` and for the `0002` migration would have caught the two most impactful bugs above before they reached this state.

## Legacy `bought_by` field still present alongside `bought_by_list`

Per the README ("`bought_by` can be deprecated once refactored out completely"), `Gift.bought_by` (a single `OneToOneField`) is legacy and has been superseded by `Gift.bought_by_list` (a `ManyToManyField`), but no migration removes `bought_by` from the schema, and `gifts/admin.py` still exposes it as an editable field in the admin. This isn't a bug per se, but is worth flagging as unfinished cleanup — see [Data Model](Data-Model.md#net-effect-on-the-model-today).

## Tooling note

This wiki was intended to be generated using an `ai-codex` skill collection's `deepwiki` skill, installed via `gh skill install <owner>/ai-codex deepwiki`. At the time of writing, `gh skill search deepwiki` and `gh skill search ai-codex` did not return any skill collection published under an `ai-codex` owner/path containing a `deepwiki` skill matching that description — the closest matches were unrelated `deepwiki`-named skills from other publishers (mostly wrappers around the external DeepWiki MCP/API service, i.e. tools for *querying* deepwiki.com about *other* repositories, not tools for *generating* DeepWiki-style docs for a local repo). Per the task's documented fallback, this wiki was written manually against the standard DeepWiki page structure (Overview, Architecture, Data Model, Setup, Routes/Views, Testing, Known Issues) instead.
