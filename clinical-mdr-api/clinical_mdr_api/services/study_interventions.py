"""Study Protocol Interventions service"""

import logging
from typing import Sequence

import yattag
from docx.enum.style import WD_STYLE_TYPE

from clinical_mdr_api import models
from clinical_mdr_api.models.table import Table
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.services.study_compound_selection import (
    StudyCompoundSelectionService,
)
from clinical_mdr_api.services.utils.table import table_to_docx, table_to_html

# For future LOCALIZATION
_gettext = {
    "intervention_or_arm_name": "Intervention/Arm name",
    "intervention_name": "Intervention name",
    "intervention_type": "Intervention type",
    "investigational_or_non_investigational": "Investigational or non-investigational",
    "pharmaceutical_form": "Pharmaceutical form",
    "route_of_administration": "Route of administration",
    "medical_device": "Medical-device (if applicable)",
    "trial_product_strength": "Trial product strength",
    "dose_and_frequency": "Dose and dose frequency",
    "dosing_and_administration": "Dosing instructions and administration",
    "transfer_from_other_therapy": "Transfer from other therapy",
    "sourcing": "Sourcing",
    "packaging_and_labelling": "Packaging and labelling",
    "authorisation_status_in": "Authorisation status in",
    "medical_device_template": "Administered using {device} with a {dispensedIn}",
    "trial_product_strength_template": "{value} {unit}",
    "None": "None",
    "study_interventions": "Study Interventions",
}.get

log = logging.getLogger(__name__)

# pylint: disable=no-member
DOCX_STYLES = {
    "table": ("SB Table Condensed", WD_STYLE_TYPE.TABLE),
    "header1": ("Table Header lvl1", WD_STYLE_TYPE.PARAGRAPH),
    "header2": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    None: ("Table Text", WD_STYLE_TYPE.PARAGRAPH),
}


class StudyInterventionsService:
    @property
    def current_user_id(self):
        return get_current_user_id()

    def get_table(self, study_uid: str) -> Table:
        compounds = self._get_study_compounds(study_uid)
        table = self.mk_table(compounds)
        return table

    def get_html(self, study_uid: str) -> str:
        table = self.get_table(study_uid)
        doc = table_to_html(
            table, id_="StudyInterventionsTable", title=_gettext("study_interventions")
        )
        return yattag.indent(doc.getvalue())

    def get_docx(self, study_uid: str):
        table = self.get_table(study_uid)
        docx = table_to_docx(table, DOCX_STYLES)
        return docx

    @staticmethod
    def mk_table(
        compounds: Sequence[models.StudySelectionCompound],
    ) -> Table:

        table = Table.new()
        table.num_header_rows = 1
        table.num_header_columns = 1

        r = 0
        table.data[r][0] = _gettext("intervention_or_arm_name")
        table.meta[r][0]["class"] = "header1"
        for c, _ in enumerate(compounds, start=1):
            table.data[r][c] = "?"  # TODO arm name
            table.meta[r][c]["class"] = "header2"

        r += 1
        table.data[r][0] = _gettext("intervention_name")
        table.meta[r][0]["class"] = "header2"
        for c, cmp in enumerate(compounds, start=1):
            table.data[r][c] = cmp.compound.name if cmp.compound.name else ""

        r += 1
        table.data[r][0] = _gettext("intervention_type")
        table.meta[r][0]["class"] = "header2"
        for c, cmp in enumerate(compounds, start=1):
            table.data[r][c] = cmp.typeOfTreatment.name if cmp.typeOfTreatment else ""

        r += 1
        table.data[r][0] = _gettext("investigational_or_non_investigational")
        table.meta[r][0]["class"] = "header2"
        for c, _ in enumerate(compounds, start=1):
            table.data[r][c] = "?"  # TODO

        r += 1
        table.data[r][0] = _gettext("pharmaceutical_form")
        table.meta[r][0]["class"] = "header2"
        for c, cmp in enumerate(compounds, start=1):
            table.data[r][c] = cmp.dosageForm.name if cmp.dosageForm else ""

        r += 1
        table.data[r][0] = _gettext("route_of_administration")
        table.meta[r][0]["class"] = "header2"
        for c, cmp in enumerate(compounds, start=1):
            table.data[r][c] = (
                cmp.routeOfAdministration.name if cmp.routeOfAdministration else ""
            )

        r += 1
        table.data[r][0] = _gettext("medical_device")
        table.meta[r][0]["class"] = "header2"
        for c, cmp in enumerate(compounds, start=1):
            m = {
                "device": cmp.device.name if cmp.device else _gettext("None"),
                "dispensedIn": (
                    cmp.dispensedIn.name if cmp.dispensedIn else _gettext("None")
                ),
            }
            table.data[r][c] = _gettext("medical_device_template").format_map(m)

        r += 1
        table.data[r][0] = _gettext("trial_product_strength")
        table.meta[r][0]["class"] = "header2"
        for c, cmp in enumerate(compounds, start=1):
            if cmp.strengthValue:
                m = {
                    "unit": cmp.strengthValue.unitLabel,
                    "value": cmp.strengthValue.value,
                }
                table.data[r][c] = _gettext(
                    "trial_product_strength_template"
                ).format_map(m)
            else:
                table.data[r][c] = ""

        r += 1
        table.data[r][0] = _gettext("dose_and_frequency")
        table.meta[r][0]["class"] = "header2"
        for c, _ in enumerate(compounds, start=1):
            table.data[r][c] = "?"  # TODO

        r += 1
        table.data[r][0] = _gettext("dosing_and_administration")
        table.meta[r][0]["class"] = "header2"
        for c, _ in enumerate(compounds, start=1):
            table.data[r][c] = "?"  # TODO

        r += 1
        table.data[r][0] = _gettext("transfer_from_other_therapy")
        table.meta[r][0]["class"] = "header2"
        for c, _ in enumerate(compounds, start=1):
            table.data[r][c] = "?"  # TODO

        r += 1
        table.data[r][0] = _gettext("sourcing")
        table.meta[r][0]["class"] = "header2"
        for c, _ in enumerate(compounds, start=1):
            table.data[r][c] = "?"  # TODO

        r += 1
        table.data[r][0] = _gettext("packaging_and_labelling")
        table.meta[r][0]["class"] = "header2"
        for c, _ in enumerate(compounds, start=1):
            table.data[r][c] = "?"  # TODO

        r += 1
        table.data[r][0] = _gettext("authorisation_status_in")
        table.meta[r][0]["class"] = "header2"
        for c, _ in enumerate(compounds, start=1):
            table.data[r][c] = "?"  # TODO

        return table

    def _get_study_compounds(
        self, study_uid
    ) -> Sequence[models.StudySelectionCompound]:
        return (
            StudyCompoundSelectionService(author=self.current_user_id)
            .get_all_selection(
                study_uid=study_uid,
            )
            .items
        )
