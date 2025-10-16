# vertice-db

Database layer for Vértice services.

## Installation

```bash
pip install vertice-db
```

## Usage

### Database Connection

```python
from vertice_db import create_db_connection

db = create_db_connection("postgresql+asyncpg://user:pass@localhost/db")

async with db.session() as session:
    # Use session
    pass
```

### Repository Pattern

```python
from vertice_db import BaseRepository, Base
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

async with db.session() as session:
    repo = BaseRepository(User, session)
    user = await repo.create(name="Alice")
    users = await repo.list()
```

### Redis Client

```python
from vertice_db import create_redis_client

redis = create_redis_client("redis://localhost:6379")
await redis.set("key", {"data": "value"}, ttl=300)
data = await redis.get("key")
```

## License

MIT
