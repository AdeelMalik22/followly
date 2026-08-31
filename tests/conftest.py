import os

# Configure settings before importing the application modules.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_followly.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret")
