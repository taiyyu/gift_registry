# Testing

[← Back to Home](Home.md)

## Current state

`gifts/tests.py` is a stub with **no tests**:

```python
from django.test import TestCase

# Create your tests here.
```

`apps/` has no test file at all. Running `./manage.py test` today collects zero test cases and reports success trivially — this must not be read as "the app is verified working"; on the contrary, the app currently has at least three known `NameError` bugs that any real test would immediately catch (see [Known Issues](Known-Issues.md)).

## Suggested coverage targets

If tests are added to this project, the following areas would give the most value, roughly in priority order:

### 1. `GiftListView` (`gifts/views.py`)

- A basic `GET /gifts/` test would immediately catch the `ArticleListView` `NameError` (see [Known Issues](Known-Issues.md#giftlistview-namerror-articlelistview-is-not-defined)) — currently this view returns HTTP 500 for every request, and no existing test exposes that.
- Once fixed: assert the response contains the names of `Gift` objects created in the test setup, and does **not** leak gifts from other registries if/when the view is scoped to a specific registry.

### 2. Model-level validators (`gifts/models.py`)

- `Gift.price` and `Gift.amount_paid` both use `MinValueValidator(0.0)`. Tests should confirm that `full_clean()` rejects negative values for both fields (note: plain `.save()` does **not** trigger these validators — a good test would demonstrate this gap explicitly, since `buy_gift` relies on plain `.save()`).
- Confirm the `Registry`↔`User` one-to-one constraint (a second `Registry` for the same `user` should raise an `IntegrityError`).
- Confirm `on_delete=models.SET_NULL` behavior: deleting a `User` should null out `Registry.user` and `Gift.bought_by` rather than cascading deletes.

### 3. `buy_gift(user, gift, amount_paid=None)` (`gifts/views.py`)

This is the one helper function that is internally consistent enough to unit test directly (see [Views and Routes](Views-and-Routes.md#buy_giftuser-gift-amount_paidnone)):

- Calling with no `amount_paid` should add `user` to `gift.bought_by_list` and set `fulfilled = True`.
- Calling with a partial `amount_paid` less than `price` should increment `amount_paid` and leave `fulfilled = False`.
- Calling repeatedly with partial payments that sum to `>= price` should flip `fulfilled = True` on the payment that crosses the threshold.
- A regression test for the missing over-payment guard: confirm (and document, until fixed) that `amount_paid` can currently exceed `price` with no error raised.

### 4. The other three helper functions (`create_registry`, `register_gift`, `get_unfulfilled_gifts`)

- `create_registry(user, context)` can be tested as-is (it only depends on a valid `context` dict passed in).
- `register_gift` and `get_unfulfilled_gifts` currently raise `NameError: name 'context' is not defined` on any call — a test would document this bug directly (mirroring the `GiftListView`/migration bugs) until the functions are fixed to accept a `context` parameter like `create_registry` does.

### 5. Migration testing (`gifts/migrations/0002_auto_20170730_2249.py`)

- Django's `migrate` command itself is effectively an integration test of the migration graph — running it against a database seeded with one or more `Gift` rows (created under the `0001_initial` state) would immediately surface the `NameError: name 'book' is not defined` bug in `make_many_bought_by_list` (see [Known Issues](Known-Issues.md#migration-namerror-book-is-not-defined)).
- Tools like `django-test-migrations` (not currently a dependency) could formalize this as an automated regression test; at minimum, a manual "migrate from empty → seed a Gift under 0001 → migrate to 0002" run before any release would have caught this.

### 6. `apps.views.home`

- Lower priority, since it's a static landing page, but a smoke test asserting HTTP 200 and absence of the stale `/books_*/` links (once removed — see [Known Issues](Known-Issues.md#stale-links-on-the-home-page)) would prevent regressions.

## Summary

No test infrastructure changes were made as part of generating this wiki — this page is a roadmap, not an implementation. See [Known Issues](Known-Issues.md) for the concrete bugs a future test suite (or manual QA pass) should catch first.
