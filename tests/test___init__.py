# noinspection PyUnresolvedReferences
def test_module_attributes():
    """Testing that package-level imports are as expected."""
    # Antecedent
    import admitted.site
    import admitted.page
    import admitted.element
    import admitted.models
    import admitted.exceptions

    # Behavior
    from admitted import Site, Page, Element, Request, Response, AdmittedError

    # Consequence
    assert Site is admitted.site.Site
    assert Page is admitted.page.Page
    assert Element is admitted.element.Element
    assert Request is admitted.models.Request
    assert Response is admitted.models.Response
    assert AdmittedError is admitted.exceptions.AdmittedError
