def remove_null_values(data: dict) -> dict:
    """
    Remove keys with null values from a dictionary.
    """
    return {k: v for k, v in data.items() if v is not None}
