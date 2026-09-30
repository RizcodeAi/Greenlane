from app.core.config import settings


def test_settings_loads():
    """Verify that settings loads correctly with expected defaults."""
    assert settings.DATABASE_NAME == "greenlane_db"
    assert settings.MONGODB_URL is not None
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
    assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://localhost:5173"]
    assert settings.LOG_LEVEL == "INFO"