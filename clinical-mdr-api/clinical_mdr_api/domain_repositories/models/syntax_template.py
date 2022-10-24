from neomodel.properties import StringProperty

from clinical_mdr_api.domain_repositories.models.generic import VersionValue


class SyntaxTemplateValue(VersionValue):
    __abstract_node__ = True
    guidance_text = StringProperty()
    name_plain = StringProperty()

    def get_study_count(self) -> int:
        pass
