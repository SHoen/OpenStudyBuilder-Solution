import pytest

from clinical_mdr_api.models.table import Table, TableDimension


class Undefined:
    pass


def test_table_dimension():
    td = TableDimension(lambda: Undefined)
    assert td.size == 0
    assert not list(td.keys())
    assert not list(td)

    # Getitem on non-existing index creates that item, and may extend the length of the series
    assert td[2] is Undefined  # sets index[2] to Undefined and size to 3
    keys = list(range(td.size))
    values = [Undefined, Undefined, Undefined]
    assert td.size == len(td) == 3
    assert list(td.keys()) == keys
    assert list(td) == values

    # Repeat the tests, as getitem may alter the series
    assert td[2] is Undefined
    assert list(td) == values
    assert list(td.keys()) == keys
    assert len(td) == td.size == 3

    value = "foo"

    # Deleting the last item will shrink the series
    td[5] = value
    keys = [0, 1, 2, 3, 4, 5]
    values = [Undefined, Undefined, Undefined, Undefined, Undefined, value]
    assert td[5] == value
    assert td.size == len(td) == 6
    assert list(td.keys()) == keys
    assert list(td) == values
    # Repeat the tests, as getitem may alter the series
    assert list(td.keys()) == keys
    assert td.size == len(td) == 6
    assert td[5] == value

    # Deleting the last item will shrink the series
    del td[5]
    assert td.size == 5
    assert len(td) == td.size
    assert list(td) == [Undefined] * 5

    # Modifying an item
    value = "bar"
    td[2] = value
    assert td.size == 5
    assert len(td) == td.size
    assert list(td) == [Undefined, Undefined, value, Undefined, Undefined]
    assert set(td.keys()) == set(range(td.size))

    # Adding an item
    value2 = "waz"
    td[5] = value2
    assert td.size == 6
    assert len(td) == td.size
    assert list(td) == [Undefined, Undefined, value, Undefined, Undefined, value2]
    assert set(td.keys()) == set(range(td.size))

    invalid_key = "hello"

    with pytest.raises(KeyError):
        _ = td[invalid_key]

    with pytest.raises(KeyError):
        td[invalid_key] = value


def test_table():
    table = Table.new()

    table.data[1][3] = "two; four"
    assert table.data.size == 2
    assert table.data[1].size == 4

    table.meta[1][3]["class"] = "klass"
    assert table.meta.size == 2
    assert table.meta[1].size == 4

    assert table.num_header_rows == 0
    assert table.num_header_columns == 0
