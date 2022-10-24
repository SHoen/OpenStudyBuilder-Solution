from typing import Optional

import yattag

from clinical_mdr_api.models.table import Table
from clinical_mdr_api.services.utils.docx_builder import DocxBuilder


def table_to_html(
    table: Table, id_: Optional[str] = None, title: Optional[str] = None
) -> yattag.simpledoc.SimpleDoc:

    doc, tag, _, line = yattag.Doc().ttl()
    doc.asis("<!DOCTYPE html>")

    with tag("html", lang="en"):
        if title:
            with tag("head"):
                line("title", title)

        with tag("body"):
            attrs = [("id", id_)] if id_ else []

            with tag("table", *attrs):

                if table.num_header_rows:
                    with tag("thead"):
                        td = "th"

                        for r in range(table.num_header_rows):

                            with tag("tr"):
                                for c, txt in enumerate(table.data[r]):
                                    meta = table.meta[r][c]
                                    _html_cell(line, meta, td, txt)

                with tag("tbody"):
                    for r in range(table.num_header_rows, table.data.size):

                        with tag("tr"):
                            for c, txt in enumerate(table.data[r]):
                                td = "th" if c < table.num_header_columns else "td"

                                meta = table.meta[r][c]
                                _html_cell(line, meta, td, txt)

    return doc


def _html_cell(line, meta, td, txt):
    if not meta.get("merged"):
        attrs = _meta_to_html_attrs(meta)
        line(td, txt, *attrs)


def _meta_to_html_attrs(meta):
    return (
        (a, meta[a]) for a in ("class", "colspan", "rowSpan") if meta.get(a) is not None
    )


def table_to_docx(table, styles):
    docx = DocxBuilder(styles=styles, landscape=True, margins=[0.5, 0.5, 0.5, 0.5])
    # Create table with actual number of columns and rows for all headers
    tablex = docx.create_table(
        num_rows=table.num_header_rows, num_columns=table.data[0].size
    )

    # Update header rows
    for r in range(table.num_header_rows):
        row = tablex.rows[r]

        prev_cell = None
        for c, txt in enumerate(table.data[r].values()):
            cellx = row.cells[c]
            meta = table.meta[r][c]

            if meta.get("merged") and prev_cell:
                # Merge cell with previous cell, will preserve the paragraph (text) from the previous one
                cellx = prev_cell.merge(cellx)

            else:
                cellx.text = txt

            prev_cell = cellx

        # Apply paragraph styles on all cells, looking up style names
        docx.format_row(
            row,
            [
                docx.styles[table.meta[r][c].get("class")][0]
                for c in range(table.data[r].size)
            ],
        )

        # Set row to repeat after a page break
        docx.repeat_table_header(row)

    # Append data rows
    for r in range(table.num_header_rows, table.data.size):
        row = docx.add_row(tablex, table.data[r])

        # Apply paragraph styles on all cells, looking up style names
        # Discovering meta by getitem rather than iteration, because lazily populated
        docx.format_row(
            row,
            [
                docx.styles[table.meta[r][c].get("class")][0]
                for c in range(table.data[r].size)
            ],
        )

    return docx
