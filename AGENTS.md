## Dev environment tips

- use treefmt to format all files
- make python code ruff compliant
- use pytest to test python code
- always use the minimum amount of complexity
- if judgment calls are easy to reverse make them. if not ask me first
- Match existing code style.
- Use builtin helpers getenv() over os.environ.get.
- Prefer single-purpose functions over “do everything” helpers.
- Avoid compatibility branches like PG_USER and POSTGRESQL_URL unless requested.
- Keep helpers only if reused or they simplify the code otherwise inline.
