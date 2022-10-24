from docx.enum.style import WD_STYLE_TYPE

from clinical_mdr_api.models.table import Table, TableDimension
from clinical_mdr_api.services.utils.table import table_to_docx, table_to_html

TABLE = Table(
    data=TableDimension(
        lambda: TableDimension(lambda: None),
        [
            TableDimension(
                lambda: None,
                ["Intervention name", "Metformin", "Metformin"],
            ),
            TableDimension(lambda: None),
            TableDimension(
                lambda: None,
                [
                    "Intervention type",
                    "Investigational Product",
                    "Comparative Treatment",
                ],
            ),
            TableDimension(
                lambda: None,
                [
                    "Medical-device (if applicable)",
                    "Administered using Syringe with a Cartridge",
                    "Administered using Syringe with a Cartridge",
                ],
            ),
            TableDimension(
                lambda: None,
                ["Trial product strength", "10.0 U/Kg", "10.0 U/Kg"],
            ),
        ],
    ),
    meta=TableDimension(
        lambda: TableDimension(dict),
        [
            TableDimension(
                dict,
                [{"class": "header1"}, {"class": "header2"}, {"class": "header2"}],
            ),
            TableDimension(
                dict,
                [{"class": "header2"}],
            ),
            TableDimension(
                dict,
                [{"class": "header2"}],
            ),
            TableDimension(
                dict,
            ),
            TableDimension(
                dict,
                [{"class": "header2"}],
            ),
        ],
    ),
    num_header_rows=1,
    num_header_columns=1,
)

DOCX_STYLES = {
    "table": ("SB Table Condensed", WD_STYLE_TYPE.TABLE),
    "header1": ("Table Header lvl1", WD_STYLE_TYPE.PARAGRAPH),
    "header2": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    None: ("Table Text", WD_STYLE_TYPE.PARAGRAPH),
}

HTML_RESULT = [
    "<!DOCTYPE html>",
    '<html lang="en">',
    "<head>",
    "<title>",
    "Test",
    "</title>",
    "</head>",
    "<body>",
    "<table>",
    "<thead>",
    "<tr>",
    '<th class="header1">',
    "Intervention name",
    "</th>",
    '<th class="header2">',
    "Metformin",
    "</th>",
    '<th class="header2">',
    "Metformin",
    "</th>",
    "</tr>",
    "</thead>",
    "<tbody>",
    "<tr>",
    "</tr>",
    "<tr>",
    '<th class="header2">',
    "Intervention type",
    "</th>",
    "<td>",
    "Investigational Product",
    "</td>",
    "<td>",
    "Comparative Treatment",
    "</td>",
    "</tr>",
]


def test_table_to_html():
    doc = table_to_html(TABLE, title="Test")
    assert doc.result[:36] == HTML_RESULT
    assert len(doc.result) == 62


def test_table_to_docx():
    docx = table_to_docx(TABLE, DOCX_STYLES).document

    assert len(docx.tables) == 1, "expected exactly 1 table in DOCX document"

    table = docx.tables[0]
    assert len(table.columns) == 3, "expected 4 columns of table"
    assert len(table.rows) == 5, "expected 6 rows of table"

    # extract all text from the table
    doc = "\n".join([cell.text for row in table.rows for cell in row.cells])

    for r, row in enumerate(TABLE.data):
        for c, txt in enumerate(row):
            assert (
                txt in doc
            ), f"row {r} column {c} was not found in document text: {txt}"
