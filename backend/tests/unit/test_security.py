import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    password = "Password123!"
    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)
    assert not verify_password("WrongPassword123!", hashed_password)


def test_create_access_token() -> None:
    token = create_access_token("user-id")
    payload = decode_token(token)

    assert payload["sub"] == "user-id"
    assert payload["type"] == "access"
    assert payload["jti"]


def test_create_refresh_token() -> None:
    token = create_refresh_token("user-id")
    payload = decode_token(token)

    assert payload["sub"] == "user-id"
    assert payload["type"] == "refresh"
    assert payload["jti"]


def test_invalid_token_fails() -> None:
    invalid_token = "invalid.token.value"

    with pytest.raises(jwt.PyJWTError):
        decode_token(invalid_token)
