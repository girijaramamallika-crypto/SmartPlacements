import os
from urllib.parse import quote_plus

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Placement123")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "placements")

SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://"
    f"{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}@"
    f"{MYSQL_HOST}:{MYSQL_PORT}/{quote_plus(MYSQL_DATABASE)}"
)

SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "placement_secret_key"
