<!-- FRESHNESS: Always verify against official docs. Links may change. Last structured: 2026-07-28 -->

# Python 3.13+ Key Features

Quick-reference for features relevant to backend development.

## Free-Threaded Mode (PEP 703)

Python 3.13 introduced experimental free-threaded (no-GIL) builds.

### Enabling
```bash
# Build or install a free-threaded Python build
# Check whether this is a free-threaded build, and whether the GIL is off right now
# (https://docs.python.org/3/howto/free-threading-python.html, 2026-10-12):
python -c "import sys, sysconfig; print(sysconfig.get_config_var('Py_GIL_DISABLED'), sys._is_gil_enabled())"

# Run with GIL disabled:
PYTHON_GIL=0 python -X utf8 app.py
# Or:
python -X gil=0 app.py
```

### When to Use
- CPU-bound workloads that benefit from true thread parallelism.
- Data processing pipelines with heavy computation.
- ML inference serving alongside API endpoints.

### Cautions
- Still experimental in 3.13; not all C extensions are thread-safe.
- Verify that all dependencies (SQLAlchemy, Pydantic, etc.) work correctly without the GIL.
- Test thoroughly under concurrent load before deploying.
- Performance may regress for single-threaded workloads due to per-object locking overhead.

### Status in Python 3.14 (verified 2026-07-28)

PEP 779 was accepted, graduating the free-threaded build from Phase I ("experimental") to Phase II ("officially supported, still optional") starting with Python 3.14. It ships as a separate interpreter binary (`python3.14t`), not the default build -- Phase III (default, no opt-in) has no PEP or timeline yet. If an imported C extension hasn't declared itself thread-safe, the interpreter silently re-enables the GIL for the whole process rather than crashing, so the "verify thread safety first" caution above still applies on 3.14.

## JIT Compiler (Experimental)

### Enabling
```bash
# Only the environment variable is documented; `-X jit` is accepted but ignored
# (https://docs.python.org/3/using/cmdline.html, 2026-10-12):
PYTHON_JIT=1 python -X utf8 app.py
```

### Impact
- Copy-and-patch JIT compiler for hot code paths.
- May improve throughput for compute-heavy loops and numeric code.
- Negligible impact on I/O-bound web APIs (most time is spent waiting for DB/network).
- Benchmark before and after; do not assume improvement.

## Improved Error Messages

Python 3.13 provides more detailed tracebacks:
```
Traceback (most recent call last):
  File "app.py", line 10, in process_order
    total = order.items[0].price * order.items[0].quantity
            ~~~~~~~~~~~~~^^^
            NameError: ... Did you mean 'prices'?
```
- Fine-grained error location markers (caret indicators).
- Better suggestions for common mistakes (typos, missing imports).
- Improved `SyntaxError` messages for missing colons, brackets, etc.

## Type System Enhancements

### Type Aliases (PEP 695)
```python
# New syntax (3.12+)
type UserId = int
type OrderItems = list[OrderItem]
type Handler[T] = Callable[[Request], Awaitable[T]]
```

### TypeVar Defaults (PEP 696)
```python
# Type parameter with a default type (new syntax, Python 3.13+)
class Repository[T = str]:
    async def get_by_id(self, id: str) -> T | None: ...

# Pre-3.13 equivalent:
# from typing import TypeVar
# T = TypeVar("T", default=str)  # needs typing_extensions.TypeVar before 3.13
```

### @override Decorator (PEP 698)
```python
from typing import override

class PostgresOrderRepository(OrderRepository):
    @override
    async def get_by_id(self, order_id: UUID) -> Order | None:
        ...  # Type checker verifies this actually overrides a parent method
```

## Performance-Relevant Changes

| Feature | Impact | When to Use |
|---------|--------|-------------|
| Free-threaded mode | True parallelism for CPU work | CPU-bound tasks, verified thread-safe deps |
| JIT compiler | Faster hot loops | Compute-heavy code; benchmark first |
| Faster `asyncio` | Reduced event loop overhead | All async applications (automatic) |
| Compact dict | Lower memory usage | Large datasets in memory (automatic) |
| Faster `json` module | Reduced serialization overhead | JSON-heavy APIs (automatic) |

## Deployment Considerations

### Docker
```dockerfile
FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# For free-threaded mode (if needed):
# ENV PYTHON_GIL=0
```

### uv Package Manager
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
uv init --python 3.13

# Add dependencies
uv add fastapi uvicorn sqlalchemy[asyncio] alembic

# Run
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## References

- What's New in Python 3.13: https://docs.python.org/3/whatsnew/3.13.html
- PEP 703 (Free-threaded CPython): https://peps.python.org/pep-0703/
- PEP 744 (JIT Compilation): https://peps.python.org/pep-0744/
- PEP 695 (Type Parameter Syntax): https://peps.python.org/pep-0695/
- uv documentation: https://docs.astral.sh/uv/
