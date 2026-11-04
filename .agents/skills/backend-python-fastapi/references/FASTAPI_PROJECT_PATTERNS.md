<!-- FRESHNESS: Always verify against official docs. Links may change. Last structured: 2026-03 -->

# FastAPI Project Patterns

Quick-reference for project structure, dependency injection, Pydantic v2, and async patterns.

## App Factory Pattern

```python
# src/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.routers import orders, health
from app.config import get_settings
from app.dependencies.db import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.db_engine = await init_db(settings.database_url)
    app.state.session_factory = async_sessionmaker(app.state.db_engine, expire_on_commit=False)
    yield
    await close_db(app.state.db_engine)

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Order Service", version="1.0.0", lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
    )
    app.include_router(health.router, tags=["health"])
    app.include_router(orders.router, prefix="/v1", tags=["orders"])
    return app

# Served as `uvicorn app.main:create_app --factory`: no module-level `app`, so it is built once.
```

## Dependency Injection

```python
async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    # Rollback only, never commit here: see "Commit before returning" below.
    async with request.app.state.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

async def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(repository=OrderRepository(db))

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    user = await UserRepository(db).get_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/orders", status_code=201)
async def create_order(
    body: OrderCreate,
    db: AsyncSession = Depends(get_db),
    service: OrderService = Depends(get_order_service),
    user: User = Depends(get_current_user),
) -> OrderResponse:
    order = await service.create(body, user_id=user.id)  # flushes, does not commit
    response = OrderResponse.model_validate(order)
    await db.commit()
    return response
```

### Commit before returning

The status code claims the write is durable, so the commit must finish before the response starts. Code after `yield` runs after the response is sent by default, since FastAPI 0.118.0 ([advanced dependencies](https://fastapi.tiangolo.com/advanced/advanced-dependencies/), read 2026-11-03). A commit there can fail after the client already holds a 201 with no row behind it, and nothing reports it to the client. Measured 2026-11-03 on PostgreSQL 18.6, with a deferred foreign key that fails only at `COMMIT`:

| FastAPI | Commit after `yield`, default scope | Commit after `yield`, `scope="function"` | Commit in the route (above) |
|---|---|---|---|
| 0.117.1 | 500, no row | not available | 500, no row |
| 0.118.0, 0.120.4 | **201, no row** | not available | 500, no row |
| 0.121.0, 0.141.1, 0.162.0 | **201, no row** | 500, no row | 500, no row |

Commit in the route or use case, as above, because it does not depend on the FastAPI version. Build the response first, so nothing that can fail runs between the commit and the return. The dependency keeps the rollback, and the session's close discards a write nobody committed: a route that forgets the commit also returns 201 with no row, so a test for a write reads the row back through a new session on the real database.

`Depends(get_db, scope="function")` moves the exit code before the response, from 0.121.0. Check the project's lockfile first, not the installed package. It does not suit a shared session: the session is closed when the response is built, and a plain `Depends(get_db)` elsewhere in the same request gets a second session, because the scope is part of the dependency cache.

## Pydantic v2 Patterns

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from uuid import UUID
from enum import StrEnum

class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"

class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0, le=1000)

class OrderCreate(BaseModel):
    model_config = ConfigDict(strict=True)
    items: list[OrderItemCreate] = Field(min_length=1, max_length=100)
    shipping_address_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=64)

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: OrderStatus
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime
```

### Typed Settings
```python
from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    database_url: PostgresDsn
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## Async Patterns

```python
# Concurrent external calls
async def enrich_order(order: Order) -> EnrichedOrder:
    customer, products = await asyncio.gather(
        customer_client.get(order.customer_id),
        product_client.get_many(order.product_ids),
    )
    return EnrichedOrder(order=order, customer=customer, products=products)

# Background tasks
@router.post("/orders", status_code=201)
async def create_order(
    body: OrderCreate, background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    order = await service.create(body)
    response = OrderResponse.model_validate(order)
    await db.commit()  # the task must never announce an order that was not stored
    # Pass plain data; a task opens its own session if it needs one.
    background_tasks.add_task(send_order_confirmation_email, response.id)
    return response
```

## Error Handling

```python
class DomainError(Exception):
    def __init__(self, code: str, detail: str, status_code: int = 400):
        self.code, self.detail, self.status_code = code, detail, status_code

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://api.example.com/errors/{exc.code}",
            "title": exc.code.replace("_", " ").title(),
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url),
            "trace_id": request.state.trace_id,
        },
    )
```

## References

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic v2: https://docs.pydantic.dev/latest/
- pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- SQLAlchemy 2.0 async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- uvicorn: https://www.uvicorn.org/
