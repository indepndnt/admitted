def test_module_attributes():
    """Testing that package-level imports are as expected."""
    # Antecedent
    import webfetch.site, webfetch.page, webfetch.element, webfetch.exceptions

    # Behavior
    from webfetch import Site, Page, Element, WebFetchError

    # Consequence
    assert Site is webfetch.site.Site
    assert Page is webfetch.page.Page
    assert Element is webfetch.element.Element
    assert WebFetchError is webfetch.exceptions.WebFetchError
