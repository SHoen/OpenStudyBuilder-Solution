import datetime
import unittest

from neomodel import db

from clinical_mdr_api.domain.templates.timeframe_templates import TimeframeTemplateAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
    TemplateVO,
)
from clinical_mdr_api.domain_repositories.models.generic import Library
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
    TemplateParameterValue,
    TemplateParameterValueRoot,
)
from clinical_mdr_api.domain_repositories.models.timeframe_template import (
    TimeframeTemplateRoot,
)
from clinical_mdr_api.domain_repositories.templates.timeframe_template_repository import (
    TimeframeTemplateRepository,
)
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.timeframe import TimeframeCreateInput
from clinical_mdr_api.services.timeframe_templates import TimeframeTemplateService
from clinical_mdr_api.services.timeframes import TimeframeService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
)


class TestTimeframeTemplateCascade(unittest.TestCase):
    TPR_LABEL = "ParameterName"
    value_roots: list = []
    value_values: list = []

    def setUp(self):
        inject_and_clear_db("efficiency")
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        lib = Library(name="Library", is_editable=True)
        lib.save()
        self.tpr = TemplateParameter(name=self.TPR_LABEL)
        self.tpr.save()
        self.tfr = TimeframeTemplateRepository()
        self.timeframe_service = TimeframeService()
        self.timeframe_template_service = TimeframeTemplateService()

        self.library = LibraryVO(name="Library", is_editable=True)
        self.tv = TemplateVO(
            name=f"Test [{self.TPR_LABEL}]",
            name_plain=f"Test {self.TPR_LABEL}",
        )
        self.im = LibraryItemMetadataVO.get_initial_item_metadata(author="Test")
        self.ar = TimeframeTemplateAR(
            _uid=TimeframeTemplateRoot.get_next_free_uid_and_increment_counter(),
            _template=self.tv,
            _library=self.library,
            _item_metadata=self.im,
            _editable_instance=False,
        )
        self.tfr.save(self.ar)

        self.ar: TimeframeTemplateAR = self.tfr.find_by_uid_2(
            self.ar.uid, for_update=True
        )
        self.ar.approve(author="TEST")
        self.tfr.save(self.ar)

        self.ar: TimeframeTemplateAR = self.tfr.find_by_uid_2(
            self.ar.uid, for_update=True
        )
        self.ar.create_new_version(
            author="TEST", change_description="Change", template=self.tv
        )
        self.tfr.save(self.ar)

        self.ar: TimeframeTemplateAR = self.tfr.find_by_uid_2(
            self.ar.uid, for_update=True
        )
        self.ntv = TemplateVO(
            name=f"Changed Test [{self.TPR_LABEL}]",
            name_plain=f"Changed Test {self.TPR_LABEL}",
        )
        self.ar.edit_draft(
            author="TEST", change_description="Change", template=self.ntv
        )
        self.tfr.save(self.ar)

    def create_template_parameters(self, label=TPR_LABEL, count=1000):
        for i in range(count):
            vr = TemplateParameterValueRoot(uid=label + "uid__" + str(i))
            vr.save()
            vv = TemplateParameterValue(name=label + "__" + str(i))
            vv.save()
            vr.has_value.connect(self.tpr)
            vr.latest_final.connect(vv)
        for vr in self.tpr.has_value.all():
            self.value_roots.append(vr)
            vv = vr.latest_final.single()
            self.value_values.append(vv)

    def create_timeframes(self, count=100, approved=False, retired=False):
        for i in range(count):
            pv = TemplateParameterMultiSelectInput(
                templateParameter=self.TPR_LABEL,
                conjunction="",
                values=[
                    {
                        "position": 1,
                        "index": 1,
                        "name": self.value_values[i].name,
                        "type": self.TPR_LABEL,
                        "uid": self.value_roots[i].uid,
                    }
                ],
            )
            template = TimeframeCreateInput(
                timeframeTemplateUid=self.ar.uid,
                libraryName="Library",
                parameterValues=[pv],
            )

            item = self.timeframe_service.create(template)
            if approved:
                self.timeframe_service.approve(item.uid)
            if retired:
                self.timeframe_service.inactivate_final(item.uid)

    def _test__init__cascade_100(self):
        self.create_template_parameters(count=110)
        self.create_timeframes(100)
        # given

        # when
        start = datetime.datetime.now()
        self.timeframe_template_service.approve_cascade(self.ar.uid)
        end = datetime.datetime.now()
        print("100 cascades run in ", end - start)

    def test__init__cascade_10(self):
        self.create_template_parameters(count=14)
        self.create_timeframes(10)
        # given

        # when
        start = datetime.datetime.now()
        self.timeframe_template_service.approve_cascade(self.ar.uid)
        end = datetime.datetime.now()
        print("10 cascades run in ", end - start)

    def test__init__cascade_approved_10(self):
        self.create_template_parameters(count=14)
        self.create_timeframes(10, True)
        # given

        # when
        start = datetime.datetime.now()
        self.timeframe_template_service.approve_cascade(self.ar.uid)
        end = datetime.datetime.now()
        print("10 approved cascades run in ", end - start)

    def test__init__cascade_retired_10(self):
        self.create_template_parameters(count=14)
        self.create_timeframes(10, True, True)
        # given

        # when
        start = datetime.datetime.now()
        self.timeframe_template_service.approve_cascade(self.ar.uid)
        end = datetime.datetime.now()
        print("10 retired run in ", end - start)
