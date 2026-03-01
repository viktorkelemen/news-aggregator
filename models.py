from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import config

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(1000), nullable=False)
    link = Column(String(2000), unique=True, nullable=False)
    source = Column(String(200), nullable=False)
    published = Column(DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    summary = Column(Text)
    content = Column(Text)
    categories = Column(Text)
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def init_db():
    Base.metadata.create_all(engine)
