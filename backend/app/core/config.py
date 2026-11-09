from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    PAYFAST_MERCHANT_ID: str | None = None
    PAYFAST_MERCHANT_KEY: str | None = None
    PAYFAST_PASSPHRASE: str | None = None

    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()