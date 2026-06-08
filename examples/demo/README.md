# django-traceid — runnable demo

A minimal Django project showing how every log line for a request carries the
same trace id, with no code passing the id around.

## What it shows

- `TraceIdMiddleware` placed first in `MIDDLEWARE` (`demo_project/settings.py`).
- `TraceIdFilter` wired into `LOGGING` and `%(trace_id)s` in the formatter.
- An `orders` app whose view logs three lines per request — all sharing one
  trace id — and returns the id in the `X-Request-ID` response header.
- Reuse of a client-supplied id when the incoming request already carries the
  header.

## Run it

From the repository root (use Docker or a virtualenv — never system Python):

```bash
pip install -e ".[dev]"
```

Then, from this directory (`examples/demo/`):

```bash
python manage.py migrate
python manage.py runserver
```

In another terminal:

```bash
# A generated id — note every log line shares it, and it comes back in the header.
curl -i http://127.0.0.1:8000/orders/42/

# Supply your own id — the same value is reused and echoed back.
curl -i -H "X-Request-ID: my-trace-123" http://127.0.0.1:8000/orders/42/
```

Watch the `runserver` console: the three `orders` log lines for each request
are prefixed with `[trace=<id>]`, matching the `X-Request-ID` response header.
