from typing import VT, Callable, Iterator, Optional, Sequence

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class TableDimension(dict):

    default_factory: Callable[..., VT] = None
    _size: int = 0

    def __init__(
        self,
        default_factory: Callable[..., VT] = None,
        values: Optional[Sequence[VT]] = None,
    ) -> None:
        self.default_factory = default_factory
        if values:
            super().__init__(enumerate(values))
            self._size = len(values)
        else:
            super().__init__()
            self._size = 0

    @staticmethod
    def _validate_key(key: int) -> None:
        if not isinstance(key, int):
            raise KeyError(f"'{key}' is not int")
        if key < 0:
            raise KeyError(f"'{key}' is < 0")

    def __missing__(self, key: int) -> VT:
        if self.default_factory is None:
            raise KeyError(key)

        self._validate_key(key)

        # Item must be set on access too.
        # Ex.: What if default was a dict, an empty dict is returned? And you add a key to it?
        # You expect to retrieve a non-empty dict on next access. Therefore, any non-scalar defaults must be saved.
        self[key] = value = self.default_factory()
        return value

    def __setitem__(self, key: int, value: VT) -> None:
        self._validate_key(key)
        super().__setitem__(key, value)
        self._size = max(self._size, key + 1)

    def __delitem__(self, key: int) -> None:
        super().__delitem__(key)
        if self._size == key + 1:
            self._size -= 1

    def __len__(self) -> int:
        return self._size

    @property
    def size(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[VT]:
        """Iterate on values rather than keys (indexes)"""
        for i in range(self.size):
            yield self[i]

    def keys(self) -> Iterator[int]:
        """Iterate over the imaginary series of keys (indexes), as this is a loosely populated series"""
        return range(self.size)


class TableCellMetadata(BaseModel):

    col_span: int = 0
    row_span: int = 0
    klass: Optional[str] = None


class Table(BaseModel):

    data: TableDimension = Field(
        ...,
        title="Table data matrix",
        description="Table data, rows and columns, including headers. Data can be text or any.",
    )
    meta: TableDimension = Field(
        ...,
        title="Table metadata matrix",
        description="Metadata for each cell as dict.",
    )

    num_header_rows: Optional[int] = Field(
        0,
        title="Number of header rows",
        description="Number of rows from the beginning of the table used as column headers",
    )
    num_header_columns: Optional[int] = Field(
        0,
        title="Number of header columns",
        description="Number of columns from the beginning of each row used as row headers",
    )

    @classmethod
    def new(cls):
        data = TableDimension(lambda: TableDimension(lambda: None))
        meta = TableDimension(lambda: TableDimension(dict))
        return cls(data=data, meta=meta)
