def assert_list_of_str(value, message):
    """Assert value is a list of strings"""
    # pylint:disable=unused-variable
    __tracebackhide__ = True

    assert isinstance(value, list), f"{message}: not a list"
    assert value, f"{message}: empty list"
    assert all(
        map(lambda v: isinstance(v, str), value)
    ), f"{message}: not all list elements are str"
