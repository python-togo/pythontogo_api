from passlib.hash import bcrypt


def remove_null_values(data: dict) -> dict:
    """
    Remove keys with null values from a dictionary.
    """
    return {k: v for k, v in data.items() if v is not None}


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return bcrypt.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    """
    return bcrypt.verify(plain_password, hashed_password)
