import json
import os
from datetime import datetime
from typing import Optional, Tuple

from neomodel import db

from clinical_mdr_api.domain_repositories._utils import helpers
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
)


class QueryService:
    """class holding the queries for the listing endpoints."""

    @staticmethod
    def _filter_for_cdisc_ct(
        catalogue_name: Optional[str] = None,
        package: Optional[str] = None,
        after_date: Optional[str] = None,
    ) -> Tuple[str, dict]:
        """Create filter to use in cypher query"""
        filter_parameters = []
        filter_query_parameters = {}
        if catalogue_name:
            filter_by_catalogue = "toUpper(cat.name) in apoc.text.split(toUpper($catalogue_name), '[ ]*,[ ]*')"
            filter_parameters.append(filter_by_catalogue)
            filter_query_parameters["catalogue_name"] = catalogue_name
        if package:
            filter_by_package_name = "toUpper(package.name) in apoc.text.split(toUpper($package_name), '[ ]*,[ ]*')"
            filter_parameters.append(filter_by_package_name)
            filter_query_parameters["package_name"] = package
        if after_date:
            filter_by_after_date = """
                package.effective_date >= date($after_date)
            """
            filter_parameters.append(filter_by_after_date)
            filter_query_parameters["after_date"] = after_date

        filter_statements = " AND ".join(filter_parameters)
        filter_statements = (
            "WHERE " + filter_statements if len(filter_statements) > 0 else ""
        )
        return filter_statements, filter_query_parameters

    def get_metadata(self, dataset_name) -> list:
        """Get metadata for legacy (and other) datasets"""

        with open(
            os.getcwd() + "/clinical_mdr_api/listings/metadata.json",
            "r",
            encoding="UTF-8",
        ) as metadata:
            meta = json.load(metadata)

        if dataset_name:
            meta = [
                x
                for x in meta
                if x["dataset_name"] in dataset_name.replace(" ", "").lower().split(",")
            ]

        return meta

    def get_topic_codes(
        self,
        at_specific_date: Optional[datetime] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset topic_cd_def."""

        match_clause = """
            MATCH (r:ActivityInstanceRoot)-[l]->(n:ActivityInstanceValue) 
            """

        if at_specific_date:
            filter_query = """
                WHERE (type(l)='HAS_VERSION' and l.status='Final'
                      and l.start_date < datetime($at_specific_date) <= l.end_date)
                      OR (type(l)='LATEST_FINAL' and l.start_date <= datetime($at_specific_date))
            """
        else:
            filter_query = """
                WHERE type(l)='LATEST_FINAL'
            """

        alias_clause = """
        
              n.name                       as lb,
              n.topic_code                 as topic_cd,
              n.adam_param_code            as short_topic_cd,
              n.legacy_description         as description,
              n.molecular_weight           as molecular_weight,
              n.value_sas_display_format   as sas_display_format,
             CASE
              WHEN (n:FindingValue) THEN 'Findings'
              WHEN (n:InterventionValue) THEN 'Interventions'
              WHEN (n:EventValue) THEN 'Events'
              ELSE 'Other'
             END as general_domain_class,
             CASE
              WHEN (n:NumericFindingValue) THEN 'NumericFinding'
              WHEN (n:CategoricFindingValue) THEN 'CategoricFinding'
              WHEN (n:TextualFindingValue) THEN 'TextualFinding'
              WHEN (n:CompoundDosingValue) THEN 'CompoundDosing'
              ELSE 'Other'
             END as sub_domain_class,
             CASE
              WHEN (n:CompoundValue) THEN 'Compound'
              WHEN (n:LaboratoryActivityValue) THEN 'LaboratoryActivity'
              WHEN (n:RatingScaleValue) THEN 'RatingScale'
              ELSE 'Other'
             END as sub_domain_type
            ORDER BY n.name
                   
              
            """
        match_clause = match_clause + filter_query

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        if at_specific_date:
            query.parameters.update({"at_specific_date": at_specific_date})
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )

        res = (result_array, attributes_names)
        result = helpers.db_result_to_list(res)

        _total_count = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                _total_count = count_result[0][0]

        return GenericFilteringReturn.create(items=result, total_count=_total_count)

    def get_cdisc_ct_ver(
        self,
        catalogue_name: Optional[str] = None,
        after_date: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_ver."""

        match_clause = """
            MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]->(package:CTPackage)
            """
        alias_clause = """
             cat.name as ct_scope, 
             toString(date(package.effective_date)) as ct_ver,
             package.name as pkg_nm
             
            """
        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )

        res = (result_array, attributes_names)
        result = helpers.db_result_to_list(res)

        _total_count = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                _total_count = count_result[0][0]

        return GenericFilteringReturn.create(items=result, total_count=_total_count)

    def get_cdisc_ct_pkg(
        self,
        catalogue_name: Optional[str] = None,
        after_date: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_pkg."""

        match_clause = """
               MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]->(package:CTPackage)
               """
        alias_clause = """
            cat.name as pkg_scope,
            package.name as pkg_nm
            """
        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )

        res = (result_array, attributes_names)
        result = helpers.db_result_to_list(res)

        _total_count = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                _total_count = count_result[0][0]

        return GenericFilteringReturn.create(items=result, total_count=_total_count)

    def get_cdisc_ct_list(
        self,
        catalogue_name: Optional[str] = None,
        package: Optional[str] = None,
        after_date: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_list."""

        match_clause = """
        
            MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]-> (package:CTPackage)-[:CONTAINS_CODELIST]
            -> (package_codelist:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]
            -> (codelist_attributes_value:CTCodelistAttributesValue)
            """

        alias_clause = """
             
            replace(package_codelist.uid,package.uid+'_','')        as ct_cd_list_cd, 
            CASE codelist_attributes_value.extensible
              WHEN false THEN 'N'
              WHEN true THEN 'Y'
            END                                                         as ct_cd_list_extensible,
            codelist_attributes_value.name                              as ct_cd_list_nm,
            codelist_attributes_value.submission_value                  as ct_cd_list_submval,
            cat.name                                                    as ct_scope,
            toString(date(package.effective_date))                      as ct_ver,
            codelist_attributes_value.definition                        as definition,
            codelist_attributes_value.preferred_term                    as nci_pref_term,
            package.name                                                as pkg_nm,
            apoc.text.join(codelist_attributes_value.synonyms,';')      as synonyms
            """

        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, package=package, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )

        res = (result_array, attributes_names)
        result = helpers.db_result_to_list(res)

        _total_count = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                _total_count = count_result[0][0]

        return GenericFilteringReturn.create(items=result, total_count=_total_count)

    def get_cdisc_ct_val(
        self,
        catalogue_name: Optional[str] = None,
        package: Optional[str] = None,
        after_date: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_val."""

        match_clause = """

            MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]-> (package:CTPackage)-[:CONTAINS_CODELIST]
            -> (package_codelist:CTPackageCodelist)-[:CONTAINS_TERM] -> (:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]
            -> (term_attributes_value:CTTermAttributesValue)
            MATCH (package_codelist)-[:CONTAINS_ATTRIBUTES]-> (codelist_attributes_value:CTCodelistAttributesValue)
            """

        alias_clause = """

            term_attributes_value.concept_id                    as ct_cd,
            codelist_attributes_value.submission_value          as ct_cd_list_submval,
            cat.name                                            as ct_scope,
            term_attributes_value.code_submission_value         as ct_submval,
            toString(date(package.effective_date))              as ct_ver,
            term_attributes_value.definition                    as definition,
            term_attributes_value.preferred_term                as nci_pref_term,
            package.name                                        as pkg_nm,
            apoc.text.join(term_attributes_value.synonyms,';')  as synonyms

            """

        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, package=package, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )

        res = (result_array, attributes_names)
        result = helpers.db_result_to_list(res)

        _total_count = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                _total_count = count_result[0][0]

        return GenericFilteringReturn.create(items=result, total_count=_total_count)

    def get_tv(self, study_uid) -> list:
        query = """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_VISIT]->(v:StudyVisit)
        OPTIONAL MATCH  (v)-->(nr:VisitNameRoot)-[:LATEST]->(nv:VisitNameValue),
                        (v)-->(dr:StudyDayRoot)-[:LATEST]->(dv:StudyDayValue)
        RETURN toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
            'TV' AS DOMAIN,
            toInteger(v.unique_visit_number) AS VISITNUM,
            toUpper(nv.name) AS VISIT,
            toInteger(dv.value) AS VISITDY,
            NULL AS ARMCD,
            NULL AS ARM,
            toUpper(v.start_rule) AS TVSTRL,
            toUpper(v.end_rule) AS TVENRL
        ORDER BY v.unique_visit_number;

        """
        result_array = db.cypher_query(
            query=query, params={"study_uid": str(study_uid)}
        )

        return helpers.db_result_to_list(result_array)

    def get_ta(self, study_uid) -> list:
        query = """
        CALL 
            {
            MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_ELEMENT]->(se:StudyElement),
            (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(sv),
            (sv) -[:HAS_STUDY_ARM] -(sar:StudyArm)-[:STUDY_ARM_HAS_DESIGN_CELL]-(sd)
            OPTIONAL MATCH (sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd)
            OPTIONAL MATCH (sep) - [:HAS_EPOCH] - (:CTTermRoot) - [:HAS_NAME_ROOT] - (:CTTermNameRoot) -[:LATEST]- (sep_term:CTTermNameValue)
            RETURN toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
                'TA' AS DOMAIN,
                se.name AS ELEMENT,
                se.order AS ETCD,
                sep.order as TAETORD,
                sd.transition_rule AS TATRANS,
                sep_term.name AS EPOCH,
                sar.name AS ARM,
                CASE sba.branch_arm_code 
                WHEN NULL THEN sar.arm_code  
                ELSE sar.arm_code+'-'+ sba.branch_arm_code 
                END AS ARMCD,
                sba.name AS TABRANCH
                ORDER BY sar.order, sep.order
            union all
            MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_ELEMENT]->(se:StudyElement),
            (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(sv),
            (sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd),
            (sba)-[:STUDY_ARM_HAS_BRANCH_ARM]-(sar:StudyArm)-[:HAS_STUDY_ARM]-(sv)
            OPTIONAL MATCH (sep) - [:HAS_EPOCH] - (:CTTermRoot) - [:HAS_NAME_ROOT] - (:CTTermNameRoot) -[:LATEST]- (sep_term:CTTermNameValue)
            RETURN toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
                'TA' AS DOMAIN,
                se.name AS ELEMENT,
                se.order AS ETCD,
                sep.order as TAETORD,
                sd.transition_rule AS TATRANS,
                sep_term.name AS EPOCH,
                sar.name AS ARM,
                CASE sba.branch_arm_code 
                WHEN NULL THEN sar.arm_code  
                ELSE sar.arm_code+'-'+ sba.branch_arm_code 
                END AS ARMCD,
                sba.name AS TABRANCH
        }
        RETURN 
            STUDYID,
            DOMAIN,
            ELEMENT,
            ETCD,
            TAETORD,
            TATRANS,
            EPOCH,
            ARM, 
            ARMCD,
            TABRANCH
        ORDER BY ARMCD, TAETORD
            


        """
        result_array = db.cypher_query(
            query=query, params={"study_uid": str(study_uid)}
        )

        return helpers.db_result_to_list(result_array)

    def get_ti(self, study_uid) -> list:
        query = """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-->(sc:StudyCriteria)
        OPTIONAL MATCH (sc)-->(cv:CriteriaValue)<-[:LATEST]-(cr:CriteriaRoot)<--(ctr:CriteriaTemplateRoot)-->(i:CTTermRoot)-->(atr:CTTermAttributesRoot)-[:LATEST]->(atv:CTTermAttributesValue)
        WHERE atv.concept_id = 'C25532' or atv.concept_id = 'C25370'
        RETURN  toUpper(sv.study_id_prefix) + '-' + toUpper(sv.study_number) AS STUDYID,
                'TI' AS DOMAIN,
                TOUPPER(substring(atv.code_submission_value,0,1)) + toInteger(sc.order) AS IETESTCD,
                cv.name_plain AS IETEST,
                atv.code_submission_value AS IECAT,
                '' AS IESCAT,
                '' AS TIRL,
                '' AS TIVERS
        ORDER BY IETESTCD;
        """
        result_array = db.cypher_query(
            query=query, params={"study_uid": str(study_uid)}
        )

        return helpers.db_result_to_list(result_array)

    def get_ts(self, study_uid) -> list:
        query = """
        CALL {
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-->(sf:StudyField)
        OPTIONAL MATCH  (sf)-->(ctr:CTTermRoot)-->(ctar:CTTermAttributesRoot)-[:LATEST_FINAL]->(ctav:CTTermAttributesValue)<--(:CTPackageTerm)<--(:CTPackageCodelist)<--(ctp:CTPackage)
        OPTIONAL MATCH (sf)-->(dtr:DictionaryTermRoot)-->(dtv:DictionaryTermValue)
        WITH *,
        CASE sf.field_name
            WHEN 'IsAdaptiveDesign' THEN 'C146995_ADAPT'
            WHEN 'StudyStopRules' THEN 'C49698_STOPRULE'
            WHEN 'TrialPhaseCode' THEN 'C48281_TPHASE'
            WHEN 'RareDiseaseIndicator' THEN 'C126070_RDIND'
            WHEN 'StudyTitle' THEN 'C49802_TITLE'
            WHEN 'StudyTypeCode' THEN 'C142175_STYPE'
            WHEN 'TrialTypeCodes' THEN 'C49660_TTYPE'
            WHEN 'IsExtensionTrial' THEN 'C139274_EXTTIND'
            WHEN 'HealthySubjectIndicator' THEN 'C98737_HLTSUBJI'
            WHEN 'PediatricInvestigationPlanIndicator' THEN 'C126069_PIPIND'
            WHEN 'PediatricStudyIndicator' THEN 'C123632_PDSTIND'
            WHEN 'PediatricPostmarketStudyIndicator' THEN 'C123631_PDPSTIND'
            WHEN 'TherapeuticAreaCodes' THEN 'C101302_THERAREA'
            WHEN 'DiagnosisGroupCodes' THEN 'C49650_TDIGRP'
            WHEN 'PlannedMaximumAgeOfSubjects' THEN 'C49694_AGEMAX'
            WHEN 'PlannedMinimumAgeOfSubjects' THEN 'C49693_AGEMIN'
            WHEN 'NumberOfExpectedSubjects' THEN 'C49692_PLANSUB'
            WHEN 'ControlTypeCode' THEN 'C49647_TCNTRL'
            WHEN 'TrialBlindingSchemaCode' THEN 'C49658_TBLIND'
            WHEN 'InterventionModelCode' THEN 'C98746_INTMODEL'
            WHEN 'IsTrialRandomised' THEN 'C25196_RANDOM'
            WHEN 'AddOnToExistingTreatments' THEN 'C49703_ADDON'
            WHEN 'TrialIntentTypes' THEN 'C49652_TINDTP'
            WHEN 'PlannedStudyLength' THEN 'C49697_LENGTH'
            WHEN 'InterventionType' THEN 'C98747_INTTYPE'
        END AS term_uid,
        CASE
            WHEN ctr IS NOT NULL
                THEN 'CDISC'
            WHEN dtv IS NOT NULL
                THEN 'Dictionary'
            ELSE 'Not Controlled'
        END AS controlled_by
        MATCH (tr:CTTermRoot {uid:term_uid})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue) 
        RETURN DISTINCT 
        sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
        'TS' AS DOMAIN,
        tav.code_submission_value AS TSPARMCD,
        tav.name_submission_value AS TSPARM,
        controlled_by AS controlled_by,
        CASE controlled_by
        WHEN 'CDISC' THEN ctav.code_submission_value
        WHEN 'Dictionary' THEN dtv.name
        WHEN 'Not Controlled' THEN sf.value
        END AS TSVAL,
        '' AS TSVALNF,
        '' AS TSVALCD,
        '' AS TSVCDREF,
        '' AS TSVCDVER
        UNION
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective)-[:HAS_OBJECTIVE_LEVEL]->(objlv)-->(octar:CTTermAttributesRoot)-[:LATEST_FINAL]->(octav:CTTermAttributesValue) 
        MATCH (so)-[:HAS_SELECTED_OBJECTIVE]->(obj)
        RETURN
        sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
        'TS' AS DOMAIN,
        octav.code_submission_value AS TSPARMCD,
        octav.name_submission_value AS TSPARM,
        '' AS controlled_by,
        obj.name_plain AS TSVAL,
        '' AS TSVALNF,
        '' AS TSVALCD,
        '' AS TSVCDREF,
        '' AS TSVCDVER
        UNION
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_ENDPOINT]->(send)-[:HAS_ENDPOINT_LEVEL]->(endplv)-->(ectar:CTTermAttributesRoot)-[:LATEST_FINAL]->(ectav:CTTermAttributesValue) 
        MATCH (send)-[:HAS_SELECTED_TIMEFRAME]->(tf:TimeframeValue)
        MATCH (send)-[:HAS_SELECTED_ENDPOINT]->(endp:EndpointValue)
        RETURN
        sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
        'TS' AS DOMAIN,
        ectav.code_submission_value AS TSPARMCD,
        ectav.name_submission_value AS TSPARM,
        '' AS controlled_by,
        endp.name_plain + ' Time frame: ' + tf.name_plain AS TSVAL,
        '' AS TSVALNF,
        '' AS TSVALCD,
        '' AS TSVCDREF,
        '' AS TSVCDVER
        UNION 
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_COHORT]->(sch:StudyCohort)
        MATCH (tr:CTTermRoot {uid:'C126063_NCOHORT'})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
        RETURN 
            sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
            'TS' AS DOMAIN,
            tav.code_submission_value AS TSPARMCD,
            tav.name_submission_value AS TSPARM,
            '' AS controlled_by,
            count(sch) AS TSVAL,
            '' AS TSVALNF,
            '' AS TSVALCD,
            '' AS TSVCDREF,
            '' AS TSVCDVER
        UNION
        CALL 
            {
            MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue),
            (sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement),
            (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(sv),
            (sv) -[:HAS_STUDY_ARM] -(sar:StudyArm)-[:STUDY_ARM_HAS_DESIGN_CELL]-(sd)
            OPTIONAL MATCH (sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd)
            OPTIONAL MATCH (sep) - [:HAS_EPOCH] - (:CTTermRoot) - [:HAS_NAME_ROOT] - (:CTTermNameRoot) -[:LATEST]- (sep_term:CTTermNameValue)
            MATCH (tr:CTTermRoot {uid:'C98771_NARMS'})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
            RETURN distinct sr,sv, sar,sba, tav
            union all
            MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue),
            (sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement),
            (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(sv),
            (sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd),
            (sba)-[:STUDY_ARM_HAS_BRANCH_ARM]-(sar:StudyArm)-[:HAS_STUDY_ARM]-(sv)
            OPTIONAL MATCH (sep) - [:HAS_EPOCH] - (:CTTermRoot) - [:HAS_NAME_ROOT] - (:CTTermNameRoot) -[:LATEST]- (sep_term:CTTermNameValue)
            MATCH (tr:CTTermRoot {uid:'C98771_NARMS'})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
            RETURN distinct sr,sv, sar,sba, tav
            }
        with   tav, sr, sv, count(*) as counter 
        return 
            sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
            'TS' AS DOMAIN,
            tav.code_submission_value AS TSPARMCD,
            tav.name_submission_value AS TSPARM,
            '' AS controlled_by,
            counter AS TSVAL,
            '' AS TSVALNF,
            '' AS TSVALCD,
            '' AS TSVCDREF,
            '' AS TSVCDVER
        }
        RETURN *
        ORDER BY TSPARMCD
        """
        result_array = db.cypher_query(
            query=query, params={"study_uid": str(study_uid)}
        )

        return helpers.db_result_to_list(result_array)

    def get_te(self, study_uid) -> list:
        query = """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_ELEMENT]->(se:StudyElement)
        RETURN 
            toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
            'TE' AS DOMAIN,
            se.uid,
            se.order AS ETCD,
            se.name AS ELEMENT,
            se.start_rule AS TESTRL,
            se.end_rule AS TEENRL,
            se.planned_duration AS TEDUR
            ORDER BY se.order
        """
        result_array = db.cypher_query(
            query=query, params={"study_uid": str(study_uid)}
        )
        return helpers.db_result_to_list(result_array)
