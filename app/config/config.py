import os

from dotenv import load_dotenv


load_dotenv()


def _required_env(name: str) -> str:
    """Return a required environment variable or fail fast."""
    value = os.getenv(name)

    if value is None:
        raise RuntimeError(
            f"Required environment variable '{name}' is not set."
        )

    value = value.strip()

    if not value:
        raise RuntimeError(
            f"Required environment variable '{name}' is empty."
        )

    return value


class Config:
    BOT_TOKEN = _required_env("BOT_TOKEN")
    DATABASE_URL = _required_env("DATABASE_URL")

    MARZBAN_URL = _required_env("MARZBAN_URL")
    MARZBAN_PUBLIC_URL = _required_env("MARZBAN_PUBLIC_URL")
    MARZBAN_USERNAME = _required_env("MARZBAN_USERNAME")
    MARZBAN_PASSWORD = _required_env("MARZBAN_PASSWORD")


config = Config()
