"""Application main file."""
import logging
from os import environ

from fastapi import Depends, FastAPI, Request, Security, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_etag.dependency import PreconditionFailed
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import AlwaysOnSampler
from starlette.middleware import Middleware
from starlette_context.middleware import RawContextMiddleware

from clinical_mdr_api import config, exceptions, routers
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth.config import (
    OAUTH_ENABLED,
    OIDC_METADATA_URL,
    SWAGGER_UI_INIT_OAUTH,
)
from clinical_mdr_api.telemetry.traceback_middleware import ExceptionTracebackMiddleware
from clinical_mdr_api.telemetry.tracing_middleware import TracingMiddleware

ALLOW_ORIGIN_REGEX = environ.get("ALLOW_ORIGIN_REGEX")

log = logging.getLogger(__name__)

# Global dependencies, in order of execution
global_dependencies = []
if OAUTH_ENABLED:
    from clinical_mdr_api.oauth.dependencies import (
        get_authenticated_user_info,
        validate_token,
    )

    global_dependencies.append(Security(validate_token))
    global_dependencies.append(Depends(get_authenticated_user_info))

# Middlewares - please don't use app.add_middleware() as that inserts them to the beginning of the list
middlewares = [
    # Context middleware - must come before TracingMiddleware
    Middleware(RawContextMiddleware)
]

# Azure Application Insights integration for tracing
if config.APPINSIGHTS_CONNECTION:
    _EXPORTER = AzureExporter(connection_string=config.APPINSIGHTS_CONNECTION)
else:
    _EXPORTER = None

# Tracing middleware
middlewares.append(
    Middleware(
        TracingMiddleware,
        sampler=AlwaysOnSampler(),
        exporter=_EXPORTER,
        exclude_paths=["/system/healthcheck"],
    )
)


# CORS setup
# FIXME: this is only valid for local development, adjust
# this for production env.
middlewares.append(
    Middleware(
        CORSMiddleware,
        allow_origin_regex=ALLOW_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["etag", "traceresponse"],
    )
)

# Convert all uncaught exceptions to response before returning to TracingMiddleware
# All other exceptions (except Exception) can be caught by ExceptionMiddleware
# provided that an exception handler is defined below with @app.exception_handler()
# Refer to: fastapi.applications.FastAPI.build_middleware_stack()
middlewares.append(Middleware(ExceptionTracebackMiddleware))


# Create app
app = FastAPI(
    middleware=middlewares,
    dependencies=global_dependencies,
    swagger_ui_init_oauth=SWAGGER_UI_INIT_OAUTH,
    title=config.settings.app_name,
    version="1.0",
    description=f"""
## NOTICE

This license information is applicable to the swagger documentation of the clinical-mdr-api, that is the openapi.json.

## License Terms (MIT)

Copyright (C) 2022 Novo Nordisk A/S, Danish company registration no. 24256790

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Licenses and Acknowledgements for Incorporated Software

This component contains software licensed under different licenses when compiled, please refer to the third-party-licenses.md file for further information and full license texts.

## Authentication:

Supports OAuth2 [Authorization Code Flow](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1),
at paths described in the [OpenID Connect Discovery metadata document]({OIDC_METADATA_URL}).
Microsoft Identity Platform
([documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)).

Authentication can be turned off with `OAUTH_ENABLED=false` environment variable. When Authentication is turned on, all 
API requests have to provide valid bearer (JWT) token. When turned off
all endpoints accept (optional) custom header `X-Test-User-Id` which 
allows any request to inject any user id value (for testing purposes). If the header is missing, the default value 
of `unknown-user` is assumed.

    """,
)


@app.exception_handler(exceptions.MDRApiBaseException)
def mdr_api_exception_handler(
    request: Request, exception: exceptions.MDRApiBaseException
):
    """Returns an HTTP error code associated to given exception."""
    log.info("Error response %s: %s", exception.status_code, exception.msg)
    return JSONResponse(
        status_code=exception.status_code,
        content=jsonable_encoder(ErrorResponse(request, exception)),
        headers=exception.headers,
    )


@app.exception_handler(PreconditionFailed)
def precondition_failed_exception_handler(
    request: Request, exception: PreconditionFailed
):
    """Returns a 412 error when a non matching etag is passed."""
    return JSONResponse(
        status_code=status.HTTP_412_PRECONDITION_FAILED,
        content=jsonable_encoder(ErrorResponse(request, exception)),
    )


# Include routers here
app.include_router(
    routers.odm_templates_router,
    prefix="/concepts/odms/templates",
    tags=["ODM Templates"],
)
app.include_router(
    routers.odm_forms_router, prefix="/concepts/odms/forms", tags=["ODM Forms"]
)
app.include_router(
    routers.odm_item_groups_router,
    prefix="/concepts/odms/item-groups",
    tags=["ODM Item Groups"],
)
app.include_router(
    routers.odm_item_router, prefix="/concepts/odms/items", tags=["ODM Item"]
)
app.include_router(
    routers.odm_conditions_router,
    prefix="/concepts/odms/conditions",
    tags=["ODM Conditions"],
)
app.include_router(
    routers.odm_methods_router,
    prefix="/concepts/odms/methods",
    tags=["ODM Methods"],
)
app.include_router(
    routers.odm_formal_expressions_router,
    prefix="/concepts/odms/formal-expressions",
    tags=["ODM Formal Expressions"],
)
app.include_router(
    routers.odm_descriptions_router,
    prefix="/concepts/odms/descriptions",
    tags=["ODM Descriptions"],
)
app.include_router(
    routers.odm_aliases_router, prefix="/concepts/odms/aliases", tags=["ODM Aliases"]
)
app.include_router(
    routers.odm_xml_extension_router,
    prefix="/concepts/odms/xml-extensions",
    tags=["ODM XML Extensions"],
)
app.include_router(
    routers.odm_xml_extension_attribute_router,
    prefix="/concepts/odms/xml-extension-attributes",
    tags=["ODM XML Extension Attributes"],
)
app.include_router(
    routers.odm_xml_extension_tag_router,
    prefix="/concepts/odms/xml-extension-tags",
    tags=["ODM XML Extension Tags"],
)
app.include_router(
    routers.odm_metadata_router,
    prefix="/concepts/odms/metadata",
    tags=["ODM Metadata Import/Export"],
)
app.include_router(
    routers.activity_description_templates_router,
    prefix="/activity-description-templates",
    tags=["Activity Description Templates"],
)
app.include_router(
    routers.criteria_templates_router,
    prefix="/criteria-templates",
    tags=["Criteria Templates"],
)
app.include_router(routers.criteria_router, prefix="/criteria", tags=["Criteria"])
app.include_router(
    routers.objective_templates_router,
    prefix="/objective-templates",
    tags=["Objective Templates"],
)
app.include_router(routers.objectives_router, prefix="/objectives", tags=["Objectives"])
app.include_router(
    routers.endpoint_templates_router,
    prefix="/endpoint-templates",
    tags=["Endpoint Templates"],
)
app.include_router(routers.endpoints_router, prefix="/endpoints", tags=["Endpoints"])
app.include_router(
    routers.timeframe_templates_router,
    prefix="/timeframe-templates",
    tags=["Timeframe templates"],
)
app.include_router(routers.timeframes_router, prefix="/timeframes", tags=["Timeframes"])
app.include_router(routers.libraries_router, prefix="/libraries", tags=["Libraries"])
app.include_router(routers.ct_catalogues_router, prefix="/ct", tags=["CT catalogues"])
app.include_router(routers.ct_packages_router, prefix="/ct", tags=["CT packages"])
app.include_router(routers.ct_codelists_router, prefix="/ct", tags=["CT codelists"])
app.include_router(
    routers.ct_codelist_attributes_router, prefix="/ct", tags=["CT codelists"]
)
app.include_router(
    routers.ct_codelist_names_router, prefix="/ct", tags=["CT codelists"]
)
app.include_router(routers.ct_terms_router, prefix="/ct", tags=["CT terms"])
app.include_router(routers.ct_term_attributes_router, prefix="/ct", tags=["CT terms"])
app.include_router(routers.ct_term_names_router, prefix="/ct", tags=["CT terms"])
app.include_router(routers.ct_stats_router, prefix="/ct", tags=["CT stats"])
app.include_router(
    routers.dictionary_codelists_router,
    prefix="/dictionaries",
    tags=["Dictionary codelists"],
)
app.include_router(
    routers.dictionary_terms_router, prefix="/dictionaries", tags=["Dictionary terms"]
)
app.include_router(
    routers.template_parameters_router,
    prefix="/template-parameters",
    tags=["Template Parameters"],
)
app.include_router(
    routers.activity_instances_router,
    prefix="/concepts/activities",
    tags=["Activity Instances"],
)
app.include_router(
    routers.reminders_router, prefix="/concepts/activities", tags=["Reminders"]
)
app.include_router(
    routers.compound_dosings_router,
    prefix="/concepts/activities",
    tags=["Compound Dosings"],
)
app.include_router(routers.compounds_router, prefix="/concepts", tags=["Compounds"])
app.include_router(
    routers.compound_aliases_router, prefix="/concepts", tags=["Compound Aliases"]
)
app.include_router(
    routers.special_purposes_router,
    prefix="/concepts/activities",
    tags=["Special Purposes"],
)
app.include_router(
    routers.categoric_finding_router,
    prefix="/concepts/activities",
    tags=["Categoric Findings"],
)
app.include_router(
    routers.numeric_findings_router,
    prefix="/concepts/activities",
    tags=["Numeric Findings"],
)
app.include_router(
    routers.textual_findings_router,
    prefix="/concepts/activities",
    tags=["Textual Findings"],
)
app.include_router(
    routers.rating_scales_router, prefix="/concepts/activities", tags=["Rating Scales"]
)
app.include_router(
    routers.laboratory_activities_router,
    prefix="/concepts/activities",
    tags=["Laboratory Activities"],
)
app.include_router(
    routers.events_router, prefix="/concepts/activities", tags=["Events"]
)
app.include_router(
    routers.activities_router,
    prefix="/concepts/activities",
    tags=["Activities"],
)
app.include_router(
    routers.activity_sub_groups_router,
    prefix="/concepts/activities",
    tags=["Activity sub groups"],
)
app.include_router(
    routers.activity_groups_router,
    prefix="/concepts/activities",
    tags=["Activity groups"],
)
app.include_router(
    routers.numeric_values_router,
    prefix="/concepts/numeric-values",
    tags=["Numeric values"],
)
app.include_router(
    routers.numeric_values_with_unit_router,
    prefix="/concepts/numeric-values-with-unit",
    tags=["Numeric values with unit"],
)
app.include_router(
    routers.text_values_router, prefix="/concepts/text-values", tags=["Text values"]
)
app.include_router(
    routers.visit_names_router, prefix="/concepts/visit-names", tags=["Visit names"]
)
app.include_router(
    routers.study_days_router, prefix="/concepts/study-days", tags=["Study days"]
)
app.include_router(
    routers.study_weeks_router, prefix="/concepts/study-weeks", tags=["Study weeks"]
)
app.include_router(
    routers.study_duration_days_router,
    prefix="/concepts/study-duration-days",
    tags=["Study duration days"],
)
app.include_router(
    routers.study_duration_weeks_router,
    prefix="/concepts/study-duration-weeks",
    tags=["Study duration weeks"],
)
app.include_router(
    routers.time_points_router, prefix="/concepts/time-points", tags=["Time points"]
)
app.include_router(
    routers.lag_times_router, prefix="/concepts/lag-times", tags=["Lag times"]
)
app.include_router(routers.projects_router, prefix="/projects", tags=["Projects"])
app.include_router(
    routers.clinical_programmes_router,
    prefix="/clinical-programmes",
    tags=["Clinical Programmes"],
)
app.include_router(routers.admin_router, prefix="/admin", tags=["Admin"])
app.include_router(routers.brands_router, prefix="/brands", tags=["Brands"])
app.include_router(routers.studies_router, prefix="/studies", tags=["Studies"])
app.include_router(routers.study_router, prefix="/study", tags=["Study Selections"])
app.include_router(
    routers.unit_definition_router,
    prefix="/concepts/unit-definitions",
    tags=["Unit Definitions"],
)
app.include_router(
    routers.complex_template_parameter_router,
    prefix="/parameter-templates",
    tags=["Parameter templates"],
)
app.include_router(
    routers.metadata_router, prefix="/listings", tags=["Listing metadata"]
)
app.include_router(
    routers.listing_router, prefix="/listings", tags=["Listing Legacy CDW MMA"]
)
app.include_router(
    routers.sdtm_listing_router, prefix="/listings", tags=["SDTM study design listings"]
)
app.include_router(
    routers.study_listing_router, prefix="/listings", tags=["study design listings"]
)
app.include_router(
    routers.configuration_router,
    prefix="/configurations",
    tags=["configuration", "Study Fields", "Field definition"],
)

system_app = FastAPI(
    middleware=None,
    title="System info sub-application",
    version="1.0",
    description="Sub-application of system-info related endpoints that are excempt from authentication requirements.",
)

system_app.include_router(routers.system_router, tags=["System"])

app.mount("/system", system_app)
