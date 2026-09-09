# Data Model

[← Back to Home](Home.md)

All models live in `gifts/models.py`. There are two models: `Registry` and `Gift`.

## `Registry`

```python
class Registry(models.Model):
    user = models.OneToOneField(User, blank=True, null=True, on_delete=models.SET_NULL)
```

| Field  | Type                        | Notes                                                              |
|--------|------------------------------|---------------------------------------------------------------------|
| `user` | `OneToOneField(User)`        | Nullable/blankable. One registry per `User`, at most. If the user is deleted, the FK is set to `NULL` (`on_delete=models.SET_NULL`), i.e. the registry itself is **not** deleted. |

There is no `name`, `description`, `created_at`, or similar metadata on `Registry` — it currently exists purely as a join point between a `User` and their `Gift`s.

## `Gift`

```python
class Gift(models.Model):
    registry = models.ForeignKey(Registry, blank=True, null=True, on_delete=models.SET_NULL)

    name = models.CharField(max_length=200, blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.0)])

    bought_by = models.OneToOneField(User, blank=True, null=True, on_delete=models.SET_NULL)
    bought_by_list = models.ManyToManyField(User, blank=True, null=True, related_name='+')
    fulfilled = models.BooleanField(default=False)

    amount_paid = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.0)], default=0.0)
```

| Field            | Type                                    | Notes |
|-------------------|------------------------------------------|-------|
| `registry`        | `ForeignKey(Registry)`                   | Nullable/blankable. Many gifts can belong to one registry. If the registry is deleted, the gift's `registry` is set to `NULL` rather than the gift being deleted. |
| `name`            | `CharField(max_length=200)`              | Nullable/blankable — a gift with no name is allowed at the model level. |
| `price`           | `DecimalField(6,2)`                       | Must be `>= 0.0` (`MinValueValidator`). Max value ~9999.99 given `max_digits=6, decimal_places=2`. |
| `bought_by`       | `OneToOneField(User)`                     | **Legacy** single-buyer field. Nullable/blankable. Superseded by `bought_by_list` (see [migration history](#migration-history) below), but the field itself has **not** been removed from the model. |
| `bought_by_list`  | `ManyToManyField(User, related_name='+')`| Newer multi-buyer field, supports the "partial payment from multiple people" use case. `related_name='+'` means `User` gets no reverse accessor for this relation. |
| `fulfilled`       | `BooleanField(default=False)`             | Whether the gift has been fully bought/paid for. |
| `amount_paid`     | `DecimalField(6,2, default=0.0)`         | Must be `>= 0.0`. Running total of contributions toward `price`; added in migration `0002`. |

### Notes on validation

`MinValueValidator(0.0)` on `price` and `amount_paid` only enforces a **lower bound**; it does not, for example, prevent `amount_paid` from exceeding `price` (over-payment), nor does it run automatically outside of `ModelForm`/`full_clean()` validation — plain `Model.save()` calls (as used by `buy_gift`, see [Views and Routes](Views-and-Routes.md)) do **not** trigger validators. So in practice nothing currently stops `amount_paid` from going negative or over `price` when gifts are bought via `buy_gift`.

## Entity-relationship summary

```
User (django.contrib.auth) ──1───────1── Registry
                                             │
                                             │ 1
                                             │
                                             ▼ *
                                           Gift
                                          /    \
                          (legacy, 0..1) /      \ (current, 0..*)
                                        User    User
                                     bought_by  bought_by_list
```

- One `User` ↔ one `Registry` (optional both ways, via `SET_NULL`).
- One `Registry` → many `Gift`s (optional, via `SET_NULL`).
- One `Gift` → at most one legacy buyer (`bought_by`) **and independently** → many buyers (`bought_by_list`), reflecting the in-progress migration away from single-buyer semantics.

## Migration history

### `0001_initial.py`

Creates the initial schema:

- `Gift` with `id`, `name`, `price`, `fulfilled`, `bought_by` (`OneToOneField` to `AUTH_USER_MODEL`).
- `Registry` with `id`, `user` (`OneToOneField` to `AUTH_USER_MODEL`).
- Adds the `registry` FK to `Gift` (added separately from `Gift`'s initial `CreateModel`, likely to avoid a forward-reference issue between the two models).

This corresponds to the "v1" schema referenced in the project `README.md` ("Simple migration is needed from v1 to v2...").

### `0002_auto_20170730_2249.py` — v1 → v2

Adds:

- `Gift.amount_paid` (new `DecimalField`, default `0.0`).
- `Gift.bought_by_list` (new `ManyToManyField` to `AUTH_USER_MODEL`).
- A `RunPython` data migration, `make_many_bought_by_list`, intended to back-fill `bought_by_list` for every existing `Gift` from its legacy `bought_by` value:

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

**This has a bug** — see [Known Issues](Known-Issues.md#migration-namerror-book-is-not-defined) — the loop variable is `gift`, but the body references an undefined name `book`. Running this migration against a database containing any `Gift` rows will raise `NameError: name 'book' is not defined` and abort the migration. The docstring is also a leftover from an unrelated "Book/Author" example and does not describe what this migration actually does.

### Net effect on the model today

`gifts/models.py` still defines **both** `bought_by` (legacy, single buyer) and `bought_by_list` (current, multiple buyers). The README notes that `bought_by` "can be deprecated once refactored out completely," but as of this codebase, no such removal migration exists — `bought_by` remains part of the schema and the model.

See also: [Setup and Usage](Setup-and-Usage.md) for how to run migrations, and [Known Issues](Known-Issues.md) for the full bug list.
