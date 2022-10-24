import logging
import os
from collections import OrderedDict
from typing import Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import yattag
from colour import Color
from PIL import ImageFont

from clinical_mdr_api import models
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.services.study_arm_selection import StudyArmSelectionService
from clinical_mdr_api.services.study_design_cell import StudyDesignCellService
from clinical_mdr_api.services.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.services.study_epoch import StudyEpochService

# Page and margin sizes (horizontal, vertical) in millimeters
from clinical_mdr_api.services.study_visit import StudyVisitService

# A4 page size (width, height) in millimeters
A4_PORTRAIT_SIZE = (210, 297)  # https://en.wikipedia.org/wiki/ISO_216#A_series
A4_PORTRAIT_MARGINS = (25 + 15, 35 + 15)  # from NN Authoring master template
A4_LANDSCAPE_SIZE = (297, 210)
A4_LANDSCAPE_MARGINS = (15 + 15, 35 + 15)
# Point size calculations
DPI = 72.0  # Dots-per-inch of a Word document
PPI = 96.0  # Pixels-per-Inch
INCH = 25.4  # Millimeters
PIXEL_SIZE = INCH / PPI  # Millimeters

# sizing in pixels
ARM_MARGIN = 5
ARM_PADDINGS = (5, 5)
ARM_CENTER = False
ARM_COLOR_DEFAULT = "#fef8e4"
ARM_BORDER = 2

DOC_MARGIN = 5

EPOCH_MARGIN = 10
EPOCH_PADDINGS = (3, 3)
EPOCH_CENTER = True
EPOCH_COLOR_DEFAULT = "#e0f2d9"
EPOCH_BORDER = 2

ELEMENT_MARGIN = 5
ELEMENT_PADDINGS = (5, 5)
ELEMENT_CENTER = False
ELEMENT_COLOR_DEFAULT = "#d2e4f3"
ELEMENT_BORDER = 1

FONT_NAME = "Times New Roman"
FONT_FILE_NAME = "utils/LiberationSerif-Regular.ttf"
FONT_SIZE = 12  # in points
FONT_SIZE_POINT_TO_PIXELS_RATIO = PPI / DPI
LINE_SPACING = 3
TEXT_BOTTOM_EXTRA_PADDING = int(FONT_SIZE / 3)
TEXT_COLOR_LIGHT = Color("white")
TEXT_COLOR_DARK = Color("black")

# merge cell with neighbouring cell if Element id matches
MERGE_VERTICALLY = True
MERGE_HORIZONTALLY = False

ROUND_CORNERS = 5

TIMELINE_ARROW_COLOR = "#AAA"
TIMELINE_ROW_MARGINS = (FONT_SIZE, 10, FONT_SIZE, 0)
VISIT_ARROW_COLOR = "#000"
VISIT_ARROW_HEIGHT = FONT_SIZE

STYLES = {
    "text": {
        "font-family": f'"{FONT_NAME}"',
        "font-size": f"{FONT_SIZE}pt",
    },
    ".arm rect": {
        "rx": f"{ROUND_CORNERS}px",
        "ry": f"{ROUND_CORNERS}px",
        "stroke-width": f"{ARM_BORDER}px",
    },
    ".epoch rect": {
        "rx": f"{ROUND_CORNERS}px",
        "ry": f"{ROUND_CORNERS}px",
        "stroke-width": f"{EPOCH_BORDER}px",
    },
    ".element rect": {
        "rx": f"{ROUND_CORNERS}px",
        "ry": f"{ROUND_CORNERS}px",
        "stroke-width": f"{ELEMENT_BORDER}px",
    },
    ".timeline-arrow": {
        "stroke": f"{TIMELINE_ARROW_COLOR}",
        "stroke-width": "2px",
        "marker-start": "url(#arrowtail1)",
        "marker-end": "url(#arrowhead1)",
        "stroke-dasharray": "6 2",
    },
    "#arrowtail1 polyline": {
        "stroke": f"{TIMELINE_ARROW_COLOR}",
        "stroke-width": "1px",
    },
    "#arrowhead1 path": {
        "fill": f"{TIMELINE_ARROW_COLOR}",
    },
    "#arrowhead2 path": {
        "fill": f"{VISIT_ARROW_COLOR}",
    },
    ".visit-arrow": {
        "stroke": f"{VISIT_ARROW_COLOR}",
        "stroke-width": "1px",
        "marker-end": "url(#arrowhead2)",
    },
}

log = logging.getLogger(__name__)


class StudyDesignFigureService:
    """Draws an SVG image of Study Design Figure

    The easiest to model the figure is to think about it as a table with rows, columns and cells.

    Then the rows are the Study Arms, and columns are the Study Epochs and cells are Study Design cells.
    First row and column are headers.
    """

    def __init__(self):
        font_path = os.path.join(os.path.dirname(__file__), FONT_FILE_NAME)
        # Although ImageFont.truetype() expects point size, it seems we need to scale it up for calculations in pixels
        self.font_size = int(round(FONT_SIZE * FONT_SIZE_POINT_TO_PIXELS_RATIO))
        self.font = ImageFont.truetype(font_path, self.font_size)
        self._current_user_id = get_current_user_id()

    def get_svg_document(self, study_uid: str):
        """Fetches necessary data and returns the SVG drawing as text"""

        # fetch data
        study_arms = self._get_study_arms(study_uid)
        study_epochs = self._get_study_epochs(study_uid)
        study_elements = self._get_study_elements(study_uid)
        study_design_cells = self._get_study_design_cells(study_uid)
        study_visits = self._get_study_visits(study_uid)

        # organise the data
        table = self._mk_data_matrix(
            study_arms, study_epochs, study_elements, study_design_cells
        )
        visits = self._select_first_visits(study_visits, study_epochs)

        # calculate table cells
        fig_width = self._calculate_widths(table)
        doc_width, doc_height = self._calculate_cells(table, fig_width)

        # merge cells vertically
        if MERGE_VERTICALLY:
            self._merge_cells_vertically(table)

        # merge cells horizontally
        if MERGE_HORIZONTALLY:
            self._merge_cells_horizontally(table)

        # calculate timeline
        timeline, doc_height = self._mk_timeline(table, visits, doc_height)

        # finally draw the figure
        return self.draw_svg(table, timeline, doc_width, doc_height)

    def _get_study_arms(
        self, study_uid
    ) -> Mapping[str, models.StudySelectionArmWithConnectedBranchArms]:
        """Returns Study Arms as an ordered dictionary of {uid: arm}"""
        study_arms = StudyArmSelectionService(self._current_user_id).get_all_selection(
            study_uid=study_uid, sort_by={"order": True}
        )
        study_arms = OrderedDict((arm.armUid, arm) for arm in study_arms.items)
        return study_arms

    def _get_study_epochs(
        self, study_uid
    ) -> Mapping[str, models.study_epoch.StudyEpoch]:
        """Returns Study Epochs as an ordered dictionary of {uid: epoch}"""
        study_epochs = StudyEpochService(self._current_user_id).get_all_epochs(
            study_uid=study_uid, sort_by={"order": True}
        )
        study_epochs = OrderedDict((epoch.uid, epoch) for epoch in study_epochs.items)
        return study_epochs

    def _get_study_elements(
        self, study_uid
    ) -> Mapping[str, models.StudySelectionElement]:
        """Returns Study Elements as an ordered dictionary of {uid: element}"""
        study_elements = StudyElementSelectionService(
            self._current_user_id
        ).get_all_selection(study_uid=study_uid)
        study_elements = OrderedDict(
            (element.elementUid, element) for element in study_elements.items
        )
        return study_elements

    def _get_study_design_cells(self, study_uid) -> Sequence[models.StudyDesignCell]:
        """Returns a sequence of Study Design Cells"""
        study_design_cells = StudyDesignCellService(
            self._current_user_id
        ).get_all_design_cells(study_uid)
        return study_design_cells

    def _get_study_visits(
        self, study_uid: str
    ) -> Mapping[str, models.study_visit.StudyVisit]:
        """Returns Study Visits as an ordered dictionary of {uid: visit}"""
        study_visits = StudyVisitService(self._current_user_id).get_all_visits(
            study_uid
        )
        study_visits = OrderedDict((visit.uid, visit) for visit in study_visits.items)
        return study_visits

    def _mk_data_matrix(
        self, study_arms, study_epochs, study_elements, study_design_cells
    ):
        """Organize the data into a kind-of tabular format

        First row with Epochs, First Column with Study Arms, and the rest is num_epochs * num_arms cells
        with Study Elements. (top-left cell-0-0 remains empty)
        """
        table = [
            [{} for _ in range(len(study_epochs) + 1)]
            for _ in range(len(study_arms) + 1)
        ]

        for id_, epoch in study_epochs.items():
            table[0][epoch.order].update(
                klass="epoch",
                id=id_,
                text=epoch.epochName,
                colors=self._calculate_colors(epoch.colorHash or EPOCH_COLOR_DEFAULT),
                margin=EPOCH_MARGIN,
                paddings=EPOCH_PADDINGS,
            )

        for id_, arm in study_arms.items():
            table[arm.order][0].update(
                klass="arm",
                id=id_,
                text=arm.shortName or arm.name,
                colors=self._calculate_colors(arm.armColour or ARM_COLOR_DEFAULT),
                margin=ARM_MARGIN,
                paddings=ARM_PADDINGS,
            )

        for cell in study_design_cells:
            arm = study_arms.get(cell.studyArmUid)
            epoch = study_epochs.get(cell.studyEpochUid)
            element = study_elements.get(cell.studyElementUid)

            if not all((arm, epoch, element)):
                log.debug(
                    "Skipping %s, missing %s, %s or %s not in results",
                    cell.designCellUid,
                    cell.studyArmUid,
                    cell.studyEpochUid,
                    cell.studyElementUid,
                )
                continue

            table[arm.order][epoch.order].update(
                klass="element",
                id=element.elementUid,
                text=element.shortName or element.name,
                colors=self._calculate_colors(
                    element.elementColour or ELEMENT_COLOR_DEFAULT
                ),
                margin=ELEMENT_MARGIN,
                paddings=ELEMENT_PADDINGS,
            )

        return table

    @staticmethod
    def _select_first_visits(study_visits, study_epochs):
        """Returns a sequence of visit data about the first visit of each epoch"""

        visits = [{} for _ in range(len(study_epochs))]

        for id_, visit in study_visits.items():
            epoch = study_epochs.get(visit.study_epoch_uid)
            # take the first visit of each Epoch
            if epoch and not visits[epoch.order - 1].get("id"):
                visits[epoch.order - 1].update(
                    id=id_,
                    visit=visit,
                    day_label=visit.studyDayLabel,
                    week_label=visit.studyWeekLabel,
                    shot_name=visit.visitShortName,
                    type_uid=visit.visitTypeUid,
                    type_name=visit.visitTypeName,
                )

        return visits

    def _calculate_widths(self, table) -> int:
        """Updates the table matrix with calculated column widths, and returns the total page width in px

        First calculates the dimensions of text needed to fit into a specific cell.
        This gives us optimal width (full length of text without wrapping) and minimum width (the longest word of text).
        Then maximum values get aggregated per column.

        We see if the whole table (maximum width of all columns plus margins) would fit on a portrait or landscape
        A4 page, calculating first without text wrapping, but if it won't fit, also with text wrapping using the size
        of the longest (unbreakable) word in the column.

        Once we have the page size, we can divide up the remaining space between columns, so the figure always take up
        the whole width of the page.

        Updates the table matrix in place and returns the total width of the figure.
        First table row has the column widths, that all cells will have to obey.
        """
        # number of columns, also numer of epochs is n_cols - 1
        n_cols = len(table[0])

        # page sizes (less page & figure margin) in pixels
        landscape_width = (
            A4_LANDSCAPE_SIZE[0] - A4_LANDSCAPE_MARGINS[0]
        ) / PIXEL_SIZE - DOC_MARGIN * 2
        portrait_width = (
            A4_PORTRAIT_SIZE[0] - A4_PORTRAIT_MARGINS[0]
        ) / PIXEL_SIZE - DOC_MARGIN * 2

        # epochs
        for e in table[0][1:]:
            (
                e["optimal-width"],
                e["min-width"],
            ) = self._calculate_text_dimensions(e["text"])

            # add paddings to widths
            e["optimal-width"] += EPOCH_PADDINGS[0] * 2
            e["min-width"] += EPOCH_PADDINGS[0] * 2

        for row in table[1:]:
            # arms
            a = row[0]
            (
                a["optimal-width"],
                a["min-width"],
            ) = self._calculate_text_dimensions(a["text"])

            # add paddings to widths
            a["optimal-width"] += ARM_PADDINGS[0] * 2
            a["min-width"] += ARM_PADDINGS[0] * 2

            # minimum and optimal text-width of arms column
            table[0][0]["min-width"] = max(
                table[0][0].get("min-width", 0), a["min-width"]
            )
            table[0][0]["optimal-width"] = max(
                table[0][0].get("optimal-width", 0), a["optimal-width"]
            )

            # elements
            for i, e in enumerate(row[1:], start=1):
                if not e:
                    continue
                (
                    e["optimal-width"],
                    e["min-width"],
                ) = self._calculate_text_dimensions(e["text"])

                # add paddings and margin to widths
                e["optimal-width"] += ELEMENT_PADDINGS[0] * 2
                e["min-width"] += ELEMENT_PADDINGS[0] * 2

                # alter minimum and optimal widths for this epoch column
                table[0][i]["min-width"] = max(
                    table[0][i]["min-width"], e["min-width"] + ELEMENT_MARGIN * 2
                )
                table[0][i]["optimal-width"] = max(
                    table[0][i]["optimal-width"],
                    e["optimal-width"] + ELEMENT_MARGIN * 2,
                )

        margins = EPOCH_MARGIN * (n_cols - 2) + ARM_PADDINGS[0]
        min_fig_width = sum(c.get("min-width", 0) for c in table[0]) + margins
        optimal_fig_width = sum(c.get("optimal-width", 0) for c in table[0]) + margins

        if portrait_width >= optimal_fig_width:
            # optimal text-width on portrait page
            max_width = portrait_width
            fig_width = optimal_fig_width
            expand_width = max_width - fig_width
            key = "optimal-width"

        elif landscape_width >= optimal_fig_width:
            # optimal text-width on landscape page
            max_width = landscape_width
            fig_width = optimal_fig_width
            expand_width = max_width - fig_width
            key = "optimal-width"

        elif landscape_width >= min_fig_width:
            # condensed text-width on landscape page
            max_width = landscape_width
            fig_width = min_fig_width
            expand_width = max_width - fig_width
            key = "min-width"

        else:
            # minimum text-width on landscape page with overflow
            max_width = min_fig_width
            expand_width = 0
            key = "min-width"

        # Divide the remaining space between columns
        expand_per_column = int(expand_width / n_cols)
        for c in table[0]:
            c["width"] = c.get(key, 0) + expand_per_column

        # First column gets extended also by the remainder of the extra space
        table[0][0]["width"] += int(expand_width % n_cols)

        # Return total figure width
        fig_width = sum(c["width"] for c in table[0]) + margins
        if fig_width >= max_width:
            log.error(
                "Max document width is %d but figure is wider %d", max_width, fig_width
            )
        return fig_width

    def _calculate_cells(self, table, fig_width: int) -> Tuple[int, int]:
        """Flows the text of cells and calculates cell and row heights, returning figure width and height int px

        Knowing the width of each column, we can flow the text into each cell, and get the required height of each cell.

        Then we can calculate the row height as maximum height of cells within that row.
        Then we pull up the height of all cells of the row to the same height to fill the available space.

        Returns total width and height of the figure in pixels int.
        """
        # starts with arms and elements
        fig_height = ARM_MARGIN
        for row in table[1:]:
            # Elements
            paddings = ELEMENT_PADDINGS
            for i, cell in enumerate(row[1:], start=1):
                if not cell:
                    continue
                # inherit column width
                cell["width"] = table[0][i]["width"] - ELEMENT_MARGIN * 2
                # flow text and adjust cell height
                self._flow_cell(cell, paddings, center=ELEMENT_CENTER)

            # maximum cell height is row height
            row_height = max(cell.get("height", 0) for cell in row[1:])

            # Arms
            a = row[0]
            # alter arm height, and flow text to column width
            a["width"] = table[0][0]["width"]
            _, h, a["lines"] = self._flow_text(
                a["text"], table[0][0]["width"], ARM_PADDINGS, center=ARM_CENTER
            )
            # row shall be high enough to accommodate all elements
            a["height"] = max(h, row_height + ELEMENT_MARGIN * 2)

            # all element cells in the row should fill the arm height
            row_height = a["height"] - ELEMENT_MARGIN * 2
            for c in row[1:]:
                c["height"] = row_height

            fig_height += a["height"] + ARM_MARGIN

        # Epochs
        for cell in table[0][1:]:
            self._flow_cell(cell, EPOCH_PADDINGS, center=EPOCH_CENTER)

        # epochs row shall be high enough to fit the highest epoch
        row_height = (
            max(cell["height"] for cell in table[0][1:]) if len(table[0]) > 1 else 0
        )
        table[0][0]["height"] = row_height
        fig_height += row_height

        # calculate cell coordinates
        x, y = DOC_MARGIN, DOC_MARGIN
        total_width = 0
        for r, row in enumerate(table):
            for c, cell in enumerate(row):

                # add margin between Epoch columns
                if c > 1:
                    x += EPOCH_MARGIN

                cell["x"] = x
                cell["y"] = y

                # add further margin to Element boxes only (row > 0 and column > 0)
                if r and c:
                    cell["x"] += ELEMENT_MARGIN
                    cell["y"] += ELEMENT_MARGIN

                # next column
                x += table[0][c]["width"]

            total_width = max(total_width, x + DOC_MARGIN + ARM_PADDINGS[0])

            # next row
            x = DOC_MARGIN
            y += max(cell["height"] for cell in row) + ARM_MARGIN

        total_height = y + DOC_MARGIN

        # arm boxes should span the width of the whole figure
        for row in table[1:]:
            row[0]["width"] = fig_width

        # epoch boxes should span the height of the whole column
        for cell in table[0][1:]:
            cell["height"] = fig_height

        expect_width = fig_width + DOC_MARGIN * 2
        expect_height = fig_height + DOC_MARGIN * 2
        if not (total_width == expect_width and total_height == expect_height):
            log.error(
                "Figure size: expected %dx%d having %dx%d",
                expect_width,
                expect_height,
                total_width,
                total_height,
            )
        return total_width, total_height

    def _flow_cell(
        self, cell, paddings: Tuple[int, int], center: Optional[bool] = False
    ):
        """Flows text into a given width, and adjusts cell height accordingly"""
        x = 0

        # note: optimal-width includes 2*padding
        if cell["optimal-width"] <= cell["width"]:
            cell["height"] = (
                self.font_size + paddings[1] * 2 + TEXT_BOTTOM_EXTRA_PADDING
            )

            if center:
                w = self._get_text_size_px(cell["text"])[0]
                x = max(0, int((cell["width"] - paddings[0] * 2 - w) / 2))

            cell["lines"] = ((x, self.font_size, cell["text"]),)

        else:
            _, cell["height"], cell["lines"] = self._flow_text(
                cell["text"], cell["width"], paddings, center
            )

    def _flow_text(
        self,
        text: str,
        cell_width: int,
        paddings: Tuple[int, int],
        center: Optional[bool] = False,
    ) -> Tuple[int, int, Sequence[Tuple[int, int, str]]]:
        """Calculates text flow for a given width, wrapping text if necessary, optional centering

        Returns width and height of the cell (px int),
        and a sequence of (x, y, text) for each line,
        where x/y coordinates (px int) and are relative to the enclosing box.
        """
        # pylint:disable=unused-variable

        max_width = cell_width - paddings[0] * 2

        # Split text into a list of whitespace-stripped words, removing empty words (because of doubled whitespace)
        words = list(filter(None, (t.strip() for t in text.split(" "))))

        lines: List[Tuple[int, int, str]] = []
        total_width, total_height = 0, 0
        line, line_width, line_height = [], 0, 0

        # pylint:disable=unused-variable
        def newline():
            """Appends the line of text with X,Y coordinates and starts a new line"""
            nonlocal lines, total_width, total_height, line, line_width, line_height

            if line:
                x = 0
                if center and line_width < max_width:
                    x = int((max_width - line_width) / 2)

                lines.append((x, total_height + self.font_size, " ".join(line)))

                total_width = max(total_width, line_width)
                total_height += self.font_size + LINE_SPACING

            line, line_width, line_height = [], 0, 0

        while words:
            # how large is the string if we include the next word
            w, h = self._get_text_size_px(" ".join(line + [words[0]]))

            # next word fits in line, or line must have at least a single word in it
            if not line or w <= max_width:
                line.append(words.pop(0))
                line_width, line_height = w, h

            # next word won't fit into this line, start a new line
            else:
                newline()

        # finish last line
        newline()
        if lines:
            total_height = total_height - LINE_SPACING + TEXT_BOTTOM_EXTRA_PADDING

        return (
            total_width + paddings[0] * 2,
            total_height + paddings[1] * 2,
            tuple(lines),
        )

    @staticmethod
    def _merge_cells_horizontally(table):
        """Merges cells with identical Study Element horizontally"""
        # pylint:disable=unsubscriptable-object,unsupported-assignment-operation
        for row in table[1:]:
            prev_cell: Optional[Mapping] = None
            for cell in row[1:]:
                if not cell.get("id"):
                    prev_cell = None
                    continue

                if prev_cell and prev_cell["id"] == cell["id"]:
                    # merge cell with previous cell in the row
                    prev_cell["width"] += (
                        cell["width"] + ELEMENT_MARGIN * 2 + EPOCH_MARGIN
                    )
                    # remove id so draw_cell() will skipp it
                    del cell["id"]

                else:
                    prev_cell = cell

    @staticmethod
    def _merge_cells_vertically(table):
        """Merges cells with identical Study Element vertically"""
        # pylint:disable=unsubscriptable-object,unsupported-assignment-operation
        n_cols = len(table[0])
        for i in range(1, n_cols):
            prev_cell: Optional[Mapping] = None
            for row in table[1:]:
                cell = row[i]
                if not cell.get("id"):
                    prev_cell = None
                    continue

                if prev_cell and prev_cell["id"] == cell["id"]:
                    # merge cell with previous cell in the column
                    prev_cell["height"] += (
                        cell["height"] + ELEMENT_MARGIN * 2 + ARM_MARGIN
                    )
                    # remove id so draw_cell() will skipp it
                    del cell["id"]

                else:
                    prev_cell = cell

    @staticmethod
    def _calculate_colors(color: str) -> Tuple[str, str, str]:
        """Returns background, text and border colors based on the cell background color"""

        if color.startswith("#"):
            color = color[:7]

        background_color = Color(color)
        text_color = Color(color)
        border_color = Color(color)

        # Dark fill gets light text
        if text_color.luminance < 0.6:
            text_color = TEXT_COLOR_LIGHT
        # Light fill gets tark text
        else:
            text_color = TEXT_COLOR_DARK

        # Always a darkish stroke
        border_color.luminance = 0.2

        return background_color.hex, border_color.hex, text_color.hex

    def _calculate_text_dimensions(self, text) -> Tuple[int, int]:
        """Calculate optimal and minimum width of a text

        Optimal width is the width of the text without wrapping, and minimal width is the longest word.
        """
        optimal_width = self._get_text_size_px(text)[0]
        word_sizes = self._get_words_size_px(text)
        min_width = max(w[1] for w in word_sizes)
        return optimal_width, min_width

    def _get_text_size_px(self, text: str) -> Tuple[int, int]:
        """Returns width and height (in pixels) of given text if rendered with font and size"""
        return self.font.getsize(text)

    def _get_words_size_px(self, text: str) -> Tuple[Tuple[str, int, int]]:
        """Returns a tuple of (word, width, height) in pixels of each word of a text if rendered with font and size"""
        return tuple((t,) + self._get_text_size_px(t) for t in text.split(" "))

    def _mk_timeline(self, table, visits, doc_height):
        """Calculates timeline labels and arrows from Study Visits and already calculated table column dimensions

        Creates a label for every new visit type.
        A label may span multiple Epochs, if the visit type remains the same.
        Label coordinates are calculated form the width of the table columns.
        Creates an arrow below each of these labels.

        Then creates a label for the first visit of the Epoch. Coordinates calculated from column widths.
        Creates a small arrow from the label perpendicular to the larger horizontal arrow.

        Returns timeline mapping and new document height in px int.
        """

        timeline = {"labels": []}

        # construct labels every visit type - may span multiple epochs
        labels, label = [], {}
        timeline["labels"].append(labels)

        y = doc_height - DOC_MARGIN + TIMELINE_ROW_MARGINS[0]
        for c, v in enumerate(visits, start=1):
            if not v:
                # Epoch may contain no visits while drafting
                continue

            # look up epoch column
            col = table[0][c]

            if v.get("type_uid") == label.get("id"):
                # same visit type, span to next column
                label["width"] = col["x"] - label["x"] + col["width"]
                # reflow text with new width
                _, label["height"], label["lines"] = self._flow_text(
                    label["text"], label["width"], (0, 0), center=True
                )

            else:
                # a different visit type deserves a new label
                label = dict(
                    id=v.get("type_uid"),
                    klass="visit-type",
                    paddings=(0, 0),
                    text=v.get("type_name"),
                    # inherit coordinates form epoch column
                    width=col["width"],
                    x=col["x"],
                    y=y,
                )

                _, label["height"], label["lines"] = self._flow_text(
                    label["text"], label["width"], (0, 0), center=True
                )

                labels.append(label)

        # adjust labels heights to the tallest label
        row_height = max(label["height"] for label in labels) if labels else 0
        for label in labels:
            if label["height"] < row_height:
                # align vertically middle within the row
                label["y"] += int((row_height - label["height"]) / 2)

        # calculate new document height
        if labels:
            doc_height = y + row_height + DOC_MARGIN
            y += row_height + TIMELINE_ROW_MARGINS[1]

        # horizontal arrows for epoch labels
        arrows = timeline["arrows"] = []
        y_offset = -int(TIMELINE_ROW_MARGINS[1] / 2)
        for label in labels:
            arrows.append(
                dict(
                    klass="timeline-arrow",
                    x1=label["x"],
                    x2=label["x"] + label["width"] + EPOCH_MARGIN,
                    y1=y + y_offset,
                    y2=y + y_offset,
                )
            )

        # construct labels for epochs first visits
        labels = []
        timeline["labels"].append(labels)

        row_height = 0
        y += row_height + TIMELINE_ROW_MARGINS[2]
        for c, v in enumerate(visits, start=1):
            if not v:
                # Epoch may contain no visits while drafting
                continue

            # look up epoch column
            col = table[0][c]

            w, h = self._get_text_size_px(v.get("week_label"))
            x = col["x"]

            label = dict(
                id=v.get("id"),
                klass="visit-timing",
                paddings=(0, 0),
                text=v.get("week_label"),
                x=x,
                y=y,
                width=w,
                height=h,
            )
            label["lines"] = ((0, self.font_size, label["text"]),)

            labels.append(label)

            row_height = max(row_height, h)

        # calculate new document height
        if labels:
            doc_height = y + row_height + TIMELINE_ROW_MARGINS[3] + DOC_MARGIN

        # vertical arrows for visit labels
        y_offset = -row_height
        for label in labels:
            arrows.append(
                dict(
                    klass="visit-arrow",
                    x1=label["x"],
                    x2=label["x"],
                    y1=label["y"] + y_offset + VISIT_ARROW_HEIGHT,
                    y2=label["y"] + y_offset,
                )
            )

        return timeline, doc_height

    def draw_svg(self, table, timeline, doc_width, doc_height):
        """Returns the SVG drawing as text

        Study Arms drawn first, as this is the bottom layer, then Epochs, finally Cells.
        Timeline with arrows added at the end.

        Styling is collected while drawing the figure, and appended to the end of the SVG.
        """

        # Some features only work with styling in Wørd
        # Collecting style definitions while building the document then dumping them at the end
        styles = OrderedDict(STYLES)

        doc = yattag.Doc()

        with doc.tag(
            "svg",
            version="1.1",
            xmlns="http://www.w3.org/2000/svg",
            width=doc_width,
            height=doc_height,
        ):

            # Reusable definitions #
            with doc.tag("defs"):
                self._arrowhead_horizontal(doc, id_="arrowhead1")
                self._arrowhead_vertical(doc, id_="arrowhead2")
                self._arrowtail(doc, id_="arrowtail1")

            # Draw of study arms first, as the "bottom layer"
            for row in table[1:]:
                cell = row[0]
                self._draw_cell(cell, doc, styles)

            # Next draw Study Epochs
            for cell in table[0][1:]:
                self._draw_cell(cell, doc, styles)

            # Draw Study Elements on top
            for row in table[1:]:
                for cell in row[1:]:
                    if not cell.get("id"):
                        # skipp empty cells
                        continue
                    self._draw_cell(cell, doc, styles)

            # Draw labels
            for row in timeline["labels"]:
                for cell in row:
                    self._draw_label(cell, doc)

            # Draw arrows
            for arrow in timeline["arrows"]:
                self._draw_arrow(arrow, doc)

            # Append the stylesheet #
            self._append_styling(doc, styles)

        return yattag.indent(doc.getvalue())

    def _draw_cell(
        self, cell: Mapping, doc: yattag.Doc, styles: MutableMapping
    ) -> None:
        """Draws a single cell of the figure"""
        styles[f"#{cell['id']} rect"] = self._box_style(cell["colors"])
        styles[f"#{cell['id']} text"] = self._text_style(cell["colors"])

        # moving group with translate enables us to use relative coordinates with children
        with doc.tag(
            "g",
            id=cell["id"],
            klass=cell["klass"],
            transform=f"translate({cell['x']}, {cell['y']})",
        ):

            # the box of the cell
            doc.stag(
                "rect",
                x=0,
                y=0,
                width=cell["width"],
                height=cell["height"],
                # must repeat these as attributes for Wørd to render rounded corners (styling does not work)
                rx=ROUND_CORNERS,
                ry=ROUND_CORNERS,
            )

            # caption of the box
            with doc.tag("text"):
                for x, y, txt in cell["lines"]:
                    doc.line(
                        "tspan",
                        txt,
                        x=x + cell["paddings"][0],
                        y=y + cell["paddings"][1],
                    )

    @staticmethod
    def _box_style(colors: Tuple[str, str, str]) -> Dict[str, str]:
        """Returns CSS styling for rectangle based on color tuple"""
        background_color, border_color, _ = colors
        return {
            "fill": background_color,
            "stroke": border_color,
        }

    @staticmethod
    def _text_style(colors: Tuple[str, str, str]) -> Dict[str, str]:
        """Returns CSS stying for text based on color tuple"""
        _, _, text_color = colors
        return {"fill": text_color}

    @staticmethod
    def _draw_label(cell: Mapping, doc: yattag.Doc) -> None:
        """Draws a simple label"""
        # moving group with translate enables us to use relative coordinates with children
        with doc.tag(
            "g",
            id=cell["id"],
            klass=cell["klass"],
            transform=f"translate({cell['x']}, {cell['y']})",
        ):
            # caption
            with doc.tag("text"):
                for x, y, txt in cell["lines"]:
                    doc.line(
                        "tspan",
                        txt,
                        x=x + cell["paddings"][0],
                        y=y + cell["paddings"][1],
                    )

    @staticmethod
    def _draw_arrow(arrow: Mapping, doc: yattag.Doc) -> None:
        # moving group with translate enables us to use relative coordinates with children
        doc.stag(
            "line",
            klass=arrow["klass"],
            x1=arrow["x1"],
            x2=arrow["x2"],
            y1=arrow["y1"],
            y2=arrow["y2"],
        )

    @staticmethod
    def _arrowhead_horizontal(doc, id_="arrowhead"):
        """Draws an arrowhead for horizontal lines, proper renderers can rotate this, but not Wørd"""
        with doc.tag(
            "marker",
            id=id_,
            viewBox="0 0 6 6",
            refX="6",
            refY="3",
            markerWidth="6",
            markerHeight="6",
            orient="auto-start-reverse",
        ):
            doc.stag("path", d="M 0 0 L 6 3 L 0 6 z")

    @staticmethod
    def _arrowhead_vertical(doc, id_="arrowhead"):
        """Draws an arrowhead for vertical lines, because Wørd can not rotate markers"""
        with doc.tag(
            "marker",
            id=id_,
            viewBox="0 0 6 6",
            refX="3",
            refY="0",
            markerWidth="6",
            markerHeight="6",
            orient="0",
        ):
            doc.stag("path", d="M 0 6 L 3 0 L 6 6 z")

    @staticmethod
    def _arrowtail(doc, id_="arrowtail"):
        """Draws a tailing perpendicular cross onto the end of a line"""
        with doc.tag(
            "marker",
            id=id_,
            viewBox="0 0 6 6",
            refX="3",
            refY="3",
            markerWidth="6",
            markerHeight="6",
            orient="auto",
        ):
            doc.stag("polyline", points="3 0, 3 6")

    @staticmethod
    def _append_styling(doc, styles):
        """Formats styling as indented CSS text and appends it to the SVG document"""
        style = [""]  # triggers a newline

        for selector in styles:
            style.append(f"    {selector} {{")
            for k, v in styles[selector].items():
                style.append(f"      {k}: {v};")
            style.append("    }")

        style.append("  ")  # indents closing </style> tag

        # append <style> tag to document
        with doc.tag("style", type="text/css"):
            doc.text("\n".join(style))
