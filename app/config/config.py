import os
from dotenv import load_dotenv

load_dotenv()

for key, value in os.environ.items():
    if (
        "DATABASE" in key
        or "BOT" in key
        or "MARZBAN" in key
    ):
        print(repr(key), "=", repr(value))


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL")

    MARZBAN_URL = os.getenv("MARZBAN_URL")
    MARZBAN_USERNAME = os.getenv("MARZBAN_USERNAME")
    MARZBAN_PASSWORD = os.getenv("MARZBAN_PASSWORD")


config = Config()