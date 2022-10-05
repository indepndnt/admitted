def test_default_window_attributes():
    # Antecedent: import the constant
    from admitted._constants import DEFAULT_WINDOW_ATTRIBUTES

    # Behavior

    # Consequence: DEFAULT_WINDOW_ATTRIBUTES is a list of strings
    assert isinstance(DEFAULT_WINDOW_ATTRIBUTES, list)
    assert all((isinstance(value, str) for value in DEFAULT_WINDOW_ATTRIBUTES))
