def validate_positive(value):

    if value <= 0:
        raise ValueError(
            "Value must be positive."
        )

    return value