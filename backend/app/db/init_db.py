from app.db.session import engine
from app.models.base import Base
# ensure all models are imported
import app.models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully.")
