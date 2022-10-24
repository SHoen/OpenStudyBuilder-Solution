import xml.etree.ElementTree as ET

from clinical_mdr_api.tests.integration.utils.method_library import generate_study_root
from clinical_mdr_api.tests.utils.checks import (
    assert_response_content_type,
    assert_response_status_code,
)


def test_svg_response(
    app_client,
):
    study = generate_study_root()
    response = app_client.get(f"/studies/{study.uid}/design.svg", stream=True)
    assert_response_status_code(response, 200)
    assert_response_content_type(response, "image/svg+xml")
    tree = ET.parse(response.raw)
    root = tree.getroot()
    assert root.tag.split("}", 1)[-1] == "svg", "Document root tag is not SVG"
