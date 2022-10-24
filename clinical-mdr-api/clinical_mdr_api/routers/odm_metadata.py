from typing import Optional, Sequence

from fastapi import APIRouter, Body, Depends, Query, Response
from fastapi.responses import StreamingResponse

from clinical_mdr_api.domain.concepts.utils import OdmExportTo, TargetType
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.services.odm_csv_exporter import OdmCsvExporterService
from clinical_mdr_api.services.odm_xml_exporter import OdmXmlExporterService
from clinical_mdr_api.services.odm_xml_importer import OdmXmlImporterService
from clinical_mdr_api.services.unit_definition import UnitDefinitionService

router = APIRouter()

unit_definition_service = UnitDefinitionService


@router.get(
    "/xmls",
    summary="Export ODM XML",
    description="",
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_odm_xml(
    targetUid: str,
    targetType: TargetType,
    exportTo: OdmExportTo,
    allowedExtensions: Optional[Sequence[str]] = Query(None),
    stylesheet: Optional[str] = None,
    unitDefinitionService: unit_definition_service = Depends(),
):
    odm_xml_export_service = OdmXmlExporterService(
        targetUid,
        targetType,
        exportTo,
        allowedExtensions,
        stylesheet,
        unitDefinitionService,
    )
    xml = odm_xml_export_service.get_odm_xml()

    return Response(content=xml, media_type="application/xml")


@router.post(
    "/xmls",
    summary="Import ODM XML",
    description="",
    status_code=201,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def store_odm_xml(
    xml: str = Body(
        None,
        description="The ODM to store as an xml string.",
    )
):
    odm_xml_importer_service = OdmXmlImporterService(xml)
    xml = odm_xml_importer_service.store_odm_xml()

    return xml


@router.get(
    "/csvs",
    summary="Export ODM CSV",
    description="",
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_odm_csv(targetUid: str, targetType: TargetType):
    odm_csv_exporter_service = OdmCsvExporterService(targetUid, targetType)
    csv_data = odm_csv_exporter_service.get_odm_csv()

    return StreamingResponse(
        iter(csv_data),
        200,
        {"Content-Disposition": "attachment; filename=odm_metadata.csv"},
        "text/csv",
    )
