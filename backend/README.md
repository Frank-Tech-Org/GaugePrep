# Backend

Each module under `modules/` may import another module only through that module's `public.py`.
Never import another module's models, services or tasks; Import Linter fails `pnpm check` if you do.

## Endpoint tests

Every operation in `openapi.json` needs three tests, each marked with the operation's method and path (or its `operationId`):

```python
@pytest.mark.success("GET /api/v1/items/{id}")
@pytest.mark.not_found("GET /api/v1/items/{id}")
@pytest.mark.refused("GET /api/v1/items/{id}")  # another learner's data
```

`tests/test_endpoint_markers.py` fails `pnpm check` and names the operation and the missing marker. Only `GET /api/v1/health` and `GET /api/v1/openapi.json` are exempt; the list is `EXEMPT` in that file. Only `pytest.mark.<kind>("METHOD /path")` on a `test_*` function, a test class or a module-level `pytestmark` in `tests/test_*.py` counts; `from pytest import mark` is not recognised, and a skipped or xfail test does not count. Regenerate `openapi.json` when you add an endpoint.
