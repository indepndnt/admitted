def test_default_window_attributes():
    """Testing that DEFAULT_WINDOW_ATTRIBUTES is a list of strings."""
    # Antecedent
    # Behavior
    from webfetch._constants import DEFAULT_WINDOW_ATTRIBUTES

    # Consequence
    assert isinstance(DEFAULT_WINDOW_ATTRIBUTES, list)
    assert all((isinstance(value, str) for value in DEFAULT_WINDOW_ATTRIBUTES))
