from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_VERSION: str
    ROOT_ROUTE: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    REDIS_URI: str
    REDIS_TOKEN: str
    MAIL_USERNAME: str = "System Generated"
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    DANGEROUS_TOKEN: str
    DANGEROUS_MAX_AGE: int
    DOMAIN: str
    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_SECRET: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
