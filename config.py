import os

# Default to SQLite for free hosting compatibility.
# If a DATABASE_URL is provided by the host, it will be used instead.
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    "sqlite:///placement_system.db"
)

SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.getenv("SECRET_KEY", "placement_secret_key")
