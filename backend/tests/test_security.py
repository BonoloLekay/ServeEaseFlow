
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)


def test_password_is_hashed():
    password = "TestPassword123!"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)


def test_wrong_password_is_rejected():
    password = "TestPassword123!"

    hashed_password = hash_password(password)

    assert not verify_password(
        "WrongPassword123!",
        hashed_password
    )


def test_jwt_token_is_created_and_decoded():
    token = create_access_token(subject="1")

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "1"


def test_invalid_jwt_token_is_rejected():
    payload = decode_access_token("invalid.token.value")

    assert payload is None
