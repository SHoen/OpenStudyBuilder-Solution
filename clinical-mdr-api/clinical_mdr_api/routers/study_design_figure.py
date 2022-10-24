"""Study chart router."""

from fastapi import Path, Query
from fastapi.responses import Response

from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.routers import studies_router as router
from clinical_mdr_api.services.study_design_figure import StudyDesignFigureService

StudyUID = Path(None, description="The unique id of the study.")

timeUnit = Query(
    "days",
    regex="^(weeks|days)$",
    description="The preferred time unit, either days or weeks.",
)


class SVGResponse(Response):
    media_type = "image/svg+xml"


@router.get(
    "/{study_uid}/design.svg",
    summary="Builds and returns a Study Design visualization image in SVG format",
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
    response_class=SVGResponse,
)
def get_study_flowchart_html(
    response: Response,
    study_uid: str = StudyUID,
) -> str:
    response.headers[
        "Content-Disposition"
    ] = f'inline; filename="{study_uid} design.svg"'
    return StudyDesignFigureService().get_svg_document(study_uid)
