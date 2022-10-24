import logging
from collections import defaultdict
from itertools import count
from typing import List, Mapping, Sequence

import yattag
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Inches
from opencensus.trace import execution_context

from clinical_mdr_api.models import (
    CTTermName,
    StudyActivitySchedule,
    StudySelectionActivity,
    StudyVisit,
)
from clinical_mdr_api.models.table_with_headers import TableHeader, TableWithHeaders
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services.ct_term_name import CTTermNameService
from clinical_mdr_api.services.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.study_visit import StudyVisitService
from clinical_mdr_api.services.utils.docx_builder import DocxBuilder

# TODO LOCALIZATION
_ = {
    "study_epoch": "Study epoch",
    "visit_short_name": "Visit short name",
    "study_week": "Study week",
    "study_day": "Study day",
    "visit_window": "Visit window (days)",
    "protocol_flowchart": "Protocol Flowchart",
}.get

log = logging.getLogger(__name__)

# pylint: disable=no-member
DOCX_STYLES = {
    "table": ("SB Table Condensed", WD_STYLE_TYPE.TABLE),
    "header1": ("Table Header lvl1", WD_STYLE_TYPE.PARAGRAPH),
    "header2": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    "header3": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    "header4": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    "fchGroup": ("Table lvl 1", WD_STYLE_TYPE.PARAGRAPH),
    "group": ("Table lvl 2", WD_STYLE_TYPE.PARAGRAPH),
    "subGroup": ("Table lvl 3", WD_STYLE_TYPE.PARAGRAPH),
    "activity": ("Table lvl 4", WD_STYLE_TYPE.PARAGRAPH),
    "cell": ("Table Text", WD_STYLE_TYPE.PARAGRAPH),
}


class ActivityRow:
    def __init__(self, level, uid, name, show=True):
        self.level = level
        self.uid = uid
        self.name = name
        self.shown = int(show)
        self.cells = defaultdict(int)


class StudyFlowchartService:
    """Assemble and visualize Study Protocol Flowchart data"""

    def __init__(self, current_user_id: str) -> None:
        self._current_user_id = current_user_id
        self._epoch_terms = None

    def get_epoch_ct_term_names(self) -> Sequence[CTTermName]:
        tracer = execution_context.get_opencensus_tracer()
        with tracer.span("StudyFlowchartService.get_epoch_ct_term_names"):

            return (
                CTTermNameService(user=self._current_user_id)
                .get_all_ct_terms(codelist_name="Epoch")
                .items
            )

    def get_study_activity_schedules(
        self, study_uid: str
    ) -> Sequence[StudyActivitySchedule]:
        tracer = execution_context.get_opencensus_tracer()
        with tracer.span("StudyFlowchartService.get_study_activity_schedules"):

            return StudyActivityScheduleService(
                author=self._current_user_id
            ).get_all_schedules(study_uid)

    def get_study_visits(self, study_uid: str) -> GenericFilteringReturn[StudyVisit]:
        tracer = execution_context.get_opencensus_tracer()
        with tracer.span("StudyFlowchartService.get_study_visits"):

            return StudyVisitService(self._current_user_id).get_all_visits(study_uid)

    def get_study_activities(
        self, study_uid: str
    ) -> GenericFilteringReturn[StudySelectionActivity]:
        tracer = execution_context.get_opencensus_tracer()
        with tracer.span("StudyFlowchartService.get_study_activities"):

            return StudyActivitySelectionService(
                author=self._current_user_id
            ).get_all_selection(study_uid)

    @property
    def epoch_terms(self) -> Mapping[str, CTTermName]:
        """Returns a dict of Objects of Epoch term names indexed by termUid"""
        if self._epoch_terms is None:
            self._epoch_terms = {t.termUid: t for t in self.get_epoch_ct_term_names()}
        return self._epoch_terms

    def get_docx_document(self, study_uid: str, time_unit: str) -> DocxBuilder:
        table = self.get_table(study_uid, time_unit)
        assert len(table.headers)

        tracer = execution_context.get_opencensus_tracer()
        with tracer.span("StudyFlowchartService._build_docx_document"):

            docx = DocxBuilder(
                styles=DOCX_STYLES, landscape=True, margins=[0.5, 0.5, 0.5, 0.5]
            )
            # Create table with actual number of columns and rows for all headers
            tablex = docx.create_table(
                num_rows=len(table.headers), num_columns=len(table.headers[0].data) - 1
            )

            # Set width of first column
            tablex.columns[0].width = Inches(4)

            # Update header rows
            for r, header in enumerate(table.headers):
                rowx = tablex.rows[r]
                style, span = header.data.pop(0), header.spans.pop(0)

                prev_cell = None
                for txt, span, c in zip(header.data, header.spans, count()):
                    cellx = rowx.cells[c]

                    if span == 0 and prev_cell:
                        # Merge cell with previous cell, will preserve the paragraph (text) from the previous one
                        cellx = prev_cell.merge(cellx)

                    else:
                        cellx.text = txt
                        if r == 0 and c > 0:
                            # Text flow in first header row is vertical except first column
                            docx.set_vertical_cell_direction(cellx, "btLr")

                    prev_cell = cellx

                # Apply paragraph style on all cells of the row
                docx.format_row(rowx, [DOCX_STYLES[style][0]] * len(rowx.cells))

                # Set row to repeat after a page break
                docx.repeat_table_header(rowx)

            # Append data rows
            for data in table.data:
                rowx = docx.add_row(tablex, data[1:])
                # Look up actual style name, style of first column is the first member of data, "cell" otherwise
                docx.format_row(
                    rowx,
                    [DOCX_STYLES[data[0]][0]]
                    + [DOCX_STYLES["cell"][0]] * (len(data) - 2),
                )

            return docx

    def get_html_document(self, study_uid: str, time_unit: str) -> str:
        table = self.get_table(study_uid, time_unit)

        tracer = execution_context.get_opencensus_tracer()
        with tracer.span("StudyFlowchartService._build_html_document"):

            doc, tag, _text, line = yattag.Doc().ttl()
            doc.asis("<!DOCTYPE html>")

            with tag("html", lang="en"):
                with tag("head"):
                    line("title", _("protocol_flowchart"))

                with tag("body"):
                    with tag("table", id="ProtocolFlowchartTable"):
                        with tag("thead"):
                            for header in table.headers:
                                klass, span = header.data.pop(0), header.spans.pop(0)
                                with tag("tr", klass=klass):
                                    for cell, span in zip(header.data, header.spans):
                                        if span == 0:
                                            continue
                                        if span > 1:
                                            line("th", cell, colSpan=span)
                                        else:
                                            line("th", cell)

                        with tag("tbody"):
                            for row in table.data:
                                with tag("tr", klass=row.pop(0)):
                                    for i, cell in enumerate(row):
                                        line(("td" if i else "th"), str(cell))

            return yattag.indent(doc.getvalue())

    def get_table(self, study_uid: str, time_unit: str) -> TableWithHeaders:
        tracer = execution_context.get_opencensus_tracer()
        with tracer.span("StudyFlowchartService.get_table"):

            study_visits = self.get_study_visits(study_uid).items

            headers = self.get_table_headers(study_visits, time_unit)

            study_activities = self.get_study_activities(study_uid).items

            activity_schedules = defaultdict(list)
            for schedule in self.get_study_activity_schedules(study_uid):
                activity_schedules[schedule.studyActivityUid].append(
                    schedule.studyVisitUid
                )

            activity_rows = self.get_activity_rows(study_activities, activity_schedules)

            data_rows = []
            for act_row in activity_rows:
                if act_row.shown:
                    data_rows.append(
                        [act_row.level, act_row.name]
                        + [
                            act_row.cells.get(visit.uid) and "X" or ""
                            for visit in study_visits
                        ]
                    )

            return TableWithHeaders(headers=headers, data=data_rows)

    def get_table_headers(
        self, study_visits: Sequence[StudyVisit], time_unit: str
    ) -> List[TableHeader]:
        """Returns a list of TableHeaders for Study Flowchart table"""
        headers = [TableHeader(data=[f"header{i + 1}"], spans=[1]) for i in range(4)]

        # First column of headers
        headers[0].append(_("study_epoch"))
        headers[1].append(_("visit_short_name"))
        if time_unit == "days":
            headers[2].append(_("study_day"))
        else:
            headers[2].append(_("study_week"))
        headers[3].append(_("visit_window"))

        # For each visit as a column, append a cell to each of the header rows
        last_epoch_uid = None
        for visit in study_visits:
            if visit.epochUid == last_epoch_uid:
                # Same epoch as in the previous column
                headers[0].append("", span=0)

            else:
                # Use Epoch term names
                try:
                    headers[0].append(
                        self.epoch_terms[visit.epochUid].sponsorPreferredName
                    )
                except KeyError:
                    log.warning(
                        "Epoch UID '%s' was not found in epoch terms", visit.epochUid
                    )
                    headers[0].append(visit.visitTypeName)

            last_epoch_uid = visit.epochUid

            headers[1].append(visit.visitShortName)

            value = ""
            if time_unit == "days":
                if visit.studyDayNumber is not None:
                    value = f"{visit.studyDayNumber:d}"
            elif visit.studyWeekNumber is not None:
                value = f"{visit.studyWeekNumber:d}"
            headers[2].append(value)

            value = ""
            if None not in (visit.minVisitWindowValue, visit.maxVisitWindowValue):
                if visit.minVisitWindowValue * -1 == visit.maxVisitWindowValue:
                    value = f"±{visit.maxVisitWindowValue:d}"
                else:
                    value = (
                        f"{visit.minVisitWindowValue:+d}/{visit.maxVisitWindowValue:+d}"
                    )
            headers[3].append(value)

        return headers

    @staticmethod
    def get_activity_rows(
        study_activities: Sequence[StudySelectionActivity],
        activity_schedules: Mapping[str, Sequence[str]],
    ) -> List[ActivityRow]:
        """
        Returns a list of ActivityRows

        Includes all study_activity activities, but also adding parent groups before, when they change or new
        """
        rows = []
        fch_group, ass_group, ass_subgroup = None, None, None

        for study_activity in study_activities:
            # Create a row for Flowchart group if not yet created
            grp = study_activity.flowchartGroup
            if grp and (not fch_group or grp.termUid != fch_group.uid):
                ass_group = None
                ass_subgroup = None

                fch_group = ActivityRow(
                    level="fchGroup",
                    uid=grp.termUid,
                    name=grp.sponsorPreferredName,
                    show=True,
                )
                rows.append(fch_group)

            # Create a row for Activity group if not yet created
            activity = study_activity.activity
            if activity.activityGroup:
                grp = activity.activityGroup

                if grp and (not ass_group or grp.uid != ass_group.uid):
                    ass_subgroup = None

                    show = study_activity.showActivityGroupInProtocolFlowchart
                    ass_group = ActivityRow(
                        level="group", uid=grp.uid, name=grp.name, show=show
                    )
                    rows.append(ass_group)

            # Create a row for Activity subgroup if not yet created
            if activity.activitySubGroup:
                grp = activity.activitySubGroup

                if grp and (not ass_subgroup or grp.uid != ass_subgroup.uid):
                    show = study_activity.showActivitySubGroupInProtocolFlowchart
                    ass_subgroup = ActivityRow(
                        level="subGroup", uid=grp.uid, name=grp.name, show=show
                    )
                    rows.append(ass_subgroup)

                    # If shown, show all parent groups as well
                    if show:
                        if ass_group:
                            ass_group.shown += 1

            # Create a row for the Activity
            show = study_activity.showActivityInProtocolFlowchart
            ass = ActivityRow(
                level="activity", uid=activity.uid, name=activity.name, show=show
            )
            rows.append(ass)

            # If Activity is shown, show all parent groups as well (increase counter of shown)
            if show:
                if ass_subgroup:
                    ass_subgroup.shown += 1
                if ass_group:
                    ass_group.shown += 1

            # Tick cells for scheduled visits, and also tick for parent groups if activity is hidden
            for study_visit_uid in activity_schedules.get(
                study_activity.studyActivityUid, []
            ):
                ass.cells[study_visit_uid] += 1
                if not show:
                    if ass_subgroup and ass_subgroup.shown:
                        ass_subgroup.cells[study_visit_uid] += 1
                    elif ass_group and ass_group.shown:
                        ass_group.cells[study_visit_uid] += 1

        return rows
