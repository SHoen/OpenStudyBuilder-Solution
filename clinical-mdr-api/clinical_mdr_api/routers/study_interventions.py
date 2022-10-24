"""Study Protocol Interventions router"""

import os

from fastapi import Path
from fastapi.responses import HTMLResponse, StreamingResponse

from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.table import Table
from clinical_mdr_api.routers import studies_router as router
from clinical_mdr_api.services.study_interventions import StudyInterventionsService

StudyUID = Path(None, description="The unique id of the study.")


@router.get(
    "/{uid}/interventions",
    summary="Returns Study Protocol Interventions table",
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
    response_model=Table,
)
def get_study_interventions(
    uid: str = StudyUID,
) -> Table:
    return StudyInterventionsService().get_table(uid)


@router.get(
    "/{uid}/interventions.html",
    summary="Builds and returns an HTML document of Study Protocol Interventions table",
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
    response_class=HTMLResponse,
)
def get_study_interventions_html(
    uid: str = StudyUID,
) -> str:
    return StudyInterventionsService().get_html(uid)


@router.get(
    "/{uid}/interventions.docx",
    summary="Builds and returns a DOCX document of Study Protocol Interventions table",
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_study_interventions_docx(
    uid: str = StudyUID,
) -> StreamingResponse:
    docx = StudyInterventionsService().get_docx(uid)
    stream = docx.get_document_stream()
    size = stream.seek(0, os.SEEK_END)
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{uid} interventions.docx"',
            "Content-Length": f"{size:d}",
        },
    )
