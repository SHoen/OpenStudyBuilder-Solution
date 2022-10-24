from neo4j import GraphDatabase
from os import listdir, truncate
from os import environ
from neo4j.work.result import Result
from string import Template
from neo4j.work.transaction import Transaction

from datetime import datetime

DATABASE = environ.get("NEO4J_MDR_DATABASE")
DATABASE_DBNAME = environ.get("NEO4J_MDR_DATABASE_DBNAME", None)
NEO4J_MDR_CLEAR_DATABASE = environ.get("NEO4J_MDR_CLEAR_DATABASE", "false")
NEO4J_MDR_BACKUP_DATABASE = environ.get("NEO4J_MDR_BACKUP_DATABASE", "false")
CLEAR_DATABASE = NEO4J_MDR_CLEAR_DATABASE.lower() == "true"
BACKUP_DATABASE = NEO4J_MDR_BACKUP_DATABASE.lower() == "true"

uri = "neo4j://{}:{}".format(
    environ.get("NEO4J_MDR_HOST"),
    environ.get("NEO4J_MDR_BOLT_PORT")
)
driver = GraphDatabase.driver(uri, auth=(
    environ.get("NEO4J_MDR_AUTH_USER"),
    environ.get("NEO4J_MDR_AUTH_PASSWORD")
))


def run_querystring(tx: Transaction, query: str) -> None:
    tx.run(query).consume()

def run_querystring_read(tx: Transaction, query: str):
    result = tx.run(query)
    return result.data()

# Using merge so it wont fail if init is run multiple times
# Used as the default set of Template Parameter allowing the end user to create Objectif Template for example
def pre_load_template_parameter_tree(tx:Transaction):
    cypher = """
        // activity
        MERGE (activity:TemplateParameter {name: "Activity"})
        // activity sub group
        MERGE (activity_sub_group:TemplateParameter {name: "ActivitySubGroup"})
        // activity group
        MERGE (activity_group:TemplateParameter {name: "ActivityGroup"})
        // activity-instance
        MERGE (activity_instance:TemplateParameter {name: "ActivityInstance"})

        // reminders
        MERGE (reminder:TemplateParameter {name: "Reminder"})
        MERGE (reminder)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        
        // interventions
        MERGE (interventions:TemplateParameter {name: "Intervention"})
        MERGE (interventions)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        MERGE (compoundDosing:TemplateParameter {name: "CompoundDosing"})
        MERGE (compoundDosing)-[:HAS_PARENT_PARAMETER]->(interventions)
        MERGE (compound:TemplateParameter {name: "Compound"})
        MERGE (compound)-[:HAS_PARENT_PARAMETER]->(compoundDosing)
        
        // special-purposes
        MERGE (special_purposes:TemplateParameter {name: "SpecialPurpose"})
        MERGE (special_purposes)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        
        // findings
        MERGE (findings:TemplateParameter {name: "Finding"})
        MERGE (findings)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        MERGE (categoricFinding:TemplateParameter {name: "CategoricFinding"})
        MERGE (categoricFinding)-[:HAS_PARENT_PARAMETER]->(findings)
        MERGE (ratingScale:TemplateParameter {name: "RatingScale"})
        MERGE (ratingScale)-[:HAS_PARENT_PARAMETER]->(categoricFinding)
        MERGE (laboratoryActivity:TemplateParameter {name: "LaboratoryActivity"})
        MERGE (laboratoryActivity)-[:HAS_PARENT_PARAMETER]->(categoricFinding)
        MERGE (numericFinding:TemplateParameter {name: "NumericFinding"})
        MERGE (numericFinding)-[:HAS_PARENT_PARAMETER]->(findings)
        MERGE (laboratoryActivity)-[:HAS_PARENT_PARAMETER]->(numericFinding)
        MERGE (textualFinding:TemplateParameter {name: "TextualFinding"})
        MERGE (textualFinding)-[:HAS_PARENT_PARAMETER]->(findings)

        // events
        MERGE (events:TemplateParameter {name: "Event"})
        MERGE (events)-[:HAS_PARENT_PARAMETER]->(activity_instance)

        // simple concepts
        MERGE (simple_concepts:TemplateParameter {name:"SimpleConcept"})
        MERGE (numeric_values:TemplateParameter {name:"NumericValue"})
        MERGE (numeric_values)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (numeric_value_with_unit:TemplateParameter {name:"NumericValueWithUnit"})
        MERGE (numeric_value_with_unit)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (text_values:TemplateParameter {name:"TextValue"})
        MERGE (text_values)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (visit_names:TemplateParameter {name:"VisitName"})
        MERGE (visit_names)-[:HAS_PARENT_PARAMETER]->(text_values)
        MERGE (dose_value:TemplateParameter {name:"DoseValue"})
        MERGE (dose_value)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_days:TemplateParameter {name:"StudyDay"})
        MERGE (study_days)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_weeks:TemplateParameter {name:"StudyWeek"})
        MERGE (study_weeks)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_duration_days:TemplateParameter {name:"StudyDurationDays"})
        MERGE (study_duration_days)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_duration_weeks:TemplateParameter {name:"StudyDurationWeeks"})
        MERGE (study_duration_weeks)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (time_points:TemplateParameter {name:"TimePoint"})
        MERGE (time_points)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (lag_time:TemplateParameter {name:"LagTime"})
        MERGE (lag_time)-[:HAS_PARENT_PARAMETER]->(numeric_values)

        // Units
        MERGE (unit:TemplateParameter {name: "Unit"})

        // Unit subsets
        MERGE (age_unit:TemplateParameter {name: "Age Unit"})
        MERGE (age_unit)-[:HAS_PARENT_PARAMETER]->(unit)
        MERGE (study_time:TemplateParameter {name: "Study Time"})
        MERGE (study_time)-[:HAS_PARENT_PARAMETER]->(unit)
        MERGE (time_unit:TemplateParameter {name: "Time Unit"})
        MERGE (time_unit)-[:HAS_PARENT_PARAMETER]->(unit)
        MERGE (dose_unit:TemplateParameter {name: "Dose Unit"})
        MERGE (dose_unit)-[:HAS_PARENT_PARAMETER]->(unit)
        MERGE (strength_unit:TemplateParameter {name: "Strength Unit"})
        MERGE (strength_unit)-[:HAS_PARENT_PARAMETER]->(unit)
        
        // comparator
        MERGE (comparator:TemplateParameter {name: "Comparator"})

        //Study Endpoint
        MERGE (endpoint:TemplateParameter {name: "StudyEndpoint"})
    """
    run_querystring(tx, cypher)


# using merge so it wont fail if init is run multiple times.
def create_special_template_parameters(tx: Transaction):
    # (re)-creates the NA template parameter value, which is an instance of every template parameter
    cypher = """
    MERGE (r:TemplateParameterValueRoot{uid: "NA"})
    WITH r
    OPTIONAL MATCH (r)-[x:HAS_VERSION|LATEST|LATEST_FINAL]->()
    DELETE x
    WITH r
    MERGE (r)-[:LATEST]->(v:TemplateParameterValue{name: "NA"})
    MERGE (r)-[:LATEST_FINAL{change_description: "Initial version", start_date: datetime(), end_date: datetime(), status: "Final", user_initials: "Import-procedure", version: "1.0"}]->(v)
    MERGE (r)-[:HAS_VERSION{change_description: "Initial version", start_date: datetime(), end_date: datetime(), status: "Final", user_initials: "Import-procedure", version: "1.0"}]->(v)
    WITH r
    MATCH (n:TemplateParameter) 
    MERGE (n)-[:HAS_VALUE]->(r)
    """
    run_querystring(tx, cypher)

def make_db_name():
    if DATABASE_DBNAME is None or DATABASE_DBNAME.lower() == "" or DATABASE_DBNAME.lower().startswith("auto"):
        now = datetime.now()
        date_str = now.strftime("%Y.%m.%d-%H.%M")
        db_name = "{}-{}".format(DATABASE,date_str)
        print(f"Using auto-generated database name: '{db_name}'")
    else:
        db_name = DATABASE_DBNAME
        print(f"Using provided database name: '{db_name}'")
    return db_name

print("\n-- Clear and backup --")
print(f"Clear database: {CLEAR_DATABASE}")
print(f"Keep backup of database: {BACKUP_DATABASE}")
# Clear database if requested
if CLEAR_DATABASE:
    with driver.session(database="system") as session:
        querystring = "SHOW ALIASES FOR DATABASE YIELD * WHERE name='{}' RETURN database".format(DATABASE)
        db_name_reply = session.read_transaction(run_querystring_read, querystring)
        if db_name_reply:
            db_name = db_name_reply[0]["database"] 
            print(f"Dropping alias '{DATABASE}' for database '{db_name}'")
            querystring = "DROP ALIAS `{}` IF EXISTS FOR DATABASE".format(DATABASE)
            session.write_transaction(run_querystring, querystring)
            if not BACKUP_DATABASE:
                # Delete the database
                querystring = "DROP DATABASE `{}` IF EXISTS".format(db_name)
                print("Dropping database '{}'".format(db_name))
                session.write_transaction(run_querystring, querystring)
            else:
                print("Keeping database '{}'".format(db_name))
        else:
            querystring = "SHOW DATABASE `{}`".format(DATABASE)
            existing = session.read_transaction(run_querystring_read, querystring)
            if len(existing)>0:
                print("Database '{}' already exists but is not an alias".format(DATABASE))
                if BACKUP_DATABASE:
                    raise RuntimeError("Unable to keep a backup since the database is not an alias")
                else:
                    querystring = "DROP DATABASE `{}` IF EXISTS".format(DATABASE)
                    print("Dropping database '{}'".format(DATABASE))
                    session.write_transaction(run_querystring, querystring)

# Create database and alias if not exists
print("\n-- Creating database and alias --")
with driver.session(database="system") as session:
    querystring = "SHOW DATABASE `{}`".format(DATABASE)
    existing = session.read_transaction(run_querystring_read, querystring)
    if len(existing)>0:
        print("Database (or alias) '{}' already exists, skipping create step".format(DATABASE))
    else:
        new_db_name = make_db_name()
        if new_db_name.lower() == DATABASE.lower():
            raise RuntimeError("Database name and alias must be different. Provided db name: {new_db_name}, alias: {DATABASE}")
        print("Creating database '{}'".format(new_db_name))
        querystring = "CREATE DATABASE `{}` IF NOT EXISTS".format(new_db_name)
        session.write_transaction(run_querystring, querystring)
        print("Creating alias '{}' for database '{}'".format(DATABASE, new_db_name))
        querystring = "CREATE ALIAS `{}` IF NOT EXISTS FOR DATABASE `{}`".format(DATABASE, new_db_name)
        session.write_transaction(run_querystring, querystring)

# Todo: Additional system db operations (set up roles and permissions)

# TODO consider adding CALL apoc.schema.assert({},{})
# Create indexes and constraints
print("\n-- Setting up indexes and constraints on specific nodes --")
with driver.session(database=DATABASE) as session:
    for querystring in [
        # clinical-mdr-api
        # -----------------------------------------------------------------------------------------------------------------------
        "CREATE INDEX index_ActivityDescriptionTemplateValue IF NOT EXISTS FOR (n:ActivityDescriptionTemplateValue) ON (n.name)",
        "CREATE INDEX index_CriteriaTemplateValue IF NOT EXISTS FOR (n:CriteriaTemplateValue) ON (n.name)",
        "CREATE INDEX index_CriteriaValue IF NOT EXISTS FOR (n:CriteriaValue) ON (n.name)",
        "CREATE INDEX index_ObjectiveTemplateValue IF NOT EXISTS FOR (n:ObjectiveTemplateValue) ON (n.name)",
        "CREATE INDEX index_ObjectiveValue IF NOT EXISTS FOR (n:ObjectiveValue) ON (n.name)",
        "CREATE INDEX index_EndpointTemplateValue IF NOT EXISTS FOR (n:EndpointTemplateValue) ON (n.name)",
        "CREATE INDEX index_EndpointValue IF NOT EXISTS FOR (n:EndpointValue) ON (n.name)",
        "CREATE INDEX index_TimeframeTemplateValue IF NOT EXISTS FOR (n:TimeframeTemplateValue) ON (n.name)",
        "CREATE INDEX index_TimeframeValue IF NOT EXISTS FOR (n:TimeframeValue) ON (n.name)",
        "CREATE INDEX index_TemplateParameterValue IF NOT EXISTS FOR (n:TemplateParameterValue) ON (n.name)",
        "CREATE INDEX index_CTCodelistAttributesValue IF NOT EXISTS FOR (n:CTCodelistAttributesValue) ON (n.name)",
        "CREATE INDEX index_CTCodelistNameValue IF NOT EXISTS FOR (n:CTCodelistNameValue) ON (n.name)",
        "CREATE INDEX index_CTTermAttributesValue_code IF NOT EXISTS FOR (n:CTTermAttributesValue) ON (n.code_submission_value)",
        "CREATE INDEX index_CTTermAttributesValue_name IF NOT EXISTS FOR (n:CTTermAttributesValue) ON (n.name_submission_value)",
        "CREATE INDEX index_CTTermNameValue IF NOT EXISTS FOR (n:CTTermNameValue) ON (n.name)",
        "CREATE INDEX index_OdmTemplateName IF NOT EXISTS FOR (n:OdmTemplateValue) ON (n.name)",
        "CREATE INDEX index_OdmFormName IF NOT EXISTS FOR (n:OdmFormValue) ON (n.name)",
        "CREATE INDEX index_OdmItemGroupName IF NOT EXISTS FOR (n:OdmItemGroupValue) ON (n.name)",
        "CREATE INDEX index_OdmItemName IF NOT EXISTS FOR (n:OdmItemValue) ON (n.name)",
        "CREATE INDEX index_OdmDescriptionName IF NOT EXISTS FOR (n:OdmDescriptionValue) ON (n.name)",
        "CREATE INDEX index_OdmAliasName IF NOT EXISTS FOR (n:OdmAliasValue) ON (n.name)",
        "CREATE INDEX index_ActivityName IF NOT EXISTS FOR (n:ActivityValue) ON (n.name)",
        "CREATE INDEX index_ActivitySubGroupName IF NOT EXISTS FOR (n:ActivitySubGroupValue) ON (n.name)",
        "CREATE INDEX index_ActivityGroupName IF NOT EXISTS FOR (n:ActivityGroupValue) ON (n.name)",
        "CREATE INDEX index_ActivityInstanceName IF NOT EXISTS FOR (n:ActivityInstanceValue) ON (n.name)",
        "CREATE INDEX index_StudyFieldName IF NOT EXISTS FOR (n:StudyField) ON (n.field_name)",
        "CREATE INDEX index_CTConfigRoot IF NOT EXISTS FOR (n:CTConfigRoot) ON (n.uid)",
        "CREATE INDEX index_ClinicalProgramme IF NOT EXISTS FOR (n:ClinicalProgramme) ON (n.uid)",
        "CREATE INDEX index_Project IF NOT EXISTS FOR (n:Project) ON (n.uid)",
        "CREATE INDEX index_StudyRoot IF NOT EXISTS FOR (n:StudyRoot) ON (n.uid)",
        "CREATE INDEX index_StudyArm IF NOT EXISTS FOR (n:StudyArm) ON (n.uid)",
        "CREATE INDEX index_StudyCompound IF NOT EXISTS FOR (n:StudyCompound) ON (n.uid)",
        "CREATE INDEX index_StudyDesignCell IF NOT EXISTS FOR (n:StudyDesignCell) ON (n.uid)",
        "CREATE INDEX index_StudyElement IF NOT EXISTS FOR (n:StudyElement) ON (n.uid)",
        "CREATE INDEX index_StudyEndpoint IF NOT EXISTS FOR (n:StudyEndpoint) ON (n.uid)",
        "CREATE INDEX index_StudyEpoch IF NOT EXISTS FOR (n:StudyEpoch) ON (n.uid)",
        "CREATE INDEX index_StudyObjective IF NOT EXISTS FOR (n:StudyObjective) ON (n.uid)",
        "CREATE INDEX index_StudyVisit IF NOT EXISTS FOR (n:StudyVisit) ON (n.uid)",
        "CREATE INDEX index_CompoundRoot IF NOT EXISTS FOR (n:CompoundRoot) ON (n.uid)",
        "CREATE INDEX index_CompoundAliasRoot IF NOT EXISTS FOR (n:CompoundAliasRoot) ON (n.uid)",
        "CREATE INDEX index_ConceptRoot IF NOT EXISTS FOR (n:ConceptRoot) ON (n.uid)",
        "CREATE INDEX index_DictionaryCodelistRoot IF NOT EXISTS FOR (n:DictionaryCodelistRoot) ON (n.uid)",
        "CREATE INDEX index_DictionaryTermRoot IF NOT EXISTS FOR (n:DictionaryTermRoot) ON (n.uid)",
        "CREATE INDEX index_TimePointRoot IF NOT EXISTS FOR (n:TimePointRoot) ON (n.uid)",
        "CREATE INDEX index_VisitNameRoot IF NOT EXISTS FOR (n:VisitNameRoot) ON (n.uid)",
        "CREATE INDEX index_ActivityRoot IF NOT EXISTS FOR (n:ActivityRoot) ON (n.uid)",
        "CREATE INDEX index_ActivityGroupRoot IF NOT EXISTS FOR (n:ActivityGroupRoot) ON (n.uid)",
        "CREATE INDEX index_ActivitySubGroupRoot IF NOT EXISTS FOR (n:ActivitySubGroupRoot) ON (n.uid)",
        "CREATE INDEX index_ActivityInstanceRoot IF NOT EXISTS FOR (n:ActivityInstanceRoot) ON (n.uid)",
        "CREATE INDEX index_UnitDefinitionRoot IF NOT EXISTS FOR (n:UnitDefinitionRoot) ON (n.uid)",
        "CREATE INDEX index_NumericValueRoot IF NOT EXISTS FOR (n:NumericValueRoot) ON (n.uid)",
        "CREATE INDEX index_NumericValueWithUnitRoot IF NOT EXISTS FOR (n:NumericValueWithUnitRoot) ON (n.uid)",


        "CREATE CONSTRAINT constraint_Library IF NOT EXISTS ON (n:Library) ASSERT (n.name) IS NODE KEY",
        "CREATE CONSTRAINT constraint_ActivityDescriptionTemplateRoot IF NOT EXISTS ON (n:ActivityDescriptionTemplateRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_CriteriaTemplateRoot IF NOT EXISTS ON (n:CriteriaTemplateRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_CriteriaRoot IF NOT EXISTS ON (n:CriteriaRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_ObjectiveTemplateRoot IF NOT EXISTS ON (n:ObjectiveTemplateRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_ObjectiveRoot IF NOT EXISTS ON (n:ObjectiveRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_EndpointTemplateRoot IF NOT EXISTS ON (n:EndpointTemplateRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_EndpointRoot IF NOT EXISTS ON (n:EndpointRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_TimeframeTemplateRoot IF NOT EXISTS ON (n:TimeframeTemplateRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_TimeframeRoot IF NOT EXISTS ON (n:TimeframeRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_TemplateParameter IF NOT EXISTS ON (n:TemplateParameter) ASSERT (n.name) IS NODE KEY",
        "CREATE CONSTRAINT constraint_TemplateParameterValueRoot IF NOT EXISTS ON (n:TemplateParameterValueRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_CTCatalogue IF NOT EXISTS ON (n:CTCatalogue) ASSERT (n.name) IS NODE KEY",
        "CREATE CONSTRAINT constraint_CTPackage IF NOT EXISTS ON (n:CTPackage) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_CTPackageCodelist IF NOT EXISTS ON (n:CTPackageCodelist) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_CTCodelistRoot IF NOT EXISTS ON (n:CTCodelistRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_CTPackageTerm IF NOT EXISTS ON (n:CTPackageTerm) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_CTTermRoot IF NOT EXISTS ON (n:CTTermRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_OdmDescriptionRoot IF NOT EXISTS ON (n:OdmDescriptionRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_OdmAliasRoot IF NOT EXISTS ON (n:OdmAliasRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_OdmTemplateRoot IF NOT EXISTS ON (n:OdmTemplateRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_OdmFormRoot IF NOT EXISTS ON (n:OdmFormRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_OdmItemGroupRoot IF NOT EXISTS ON (n:OdmItemGroupRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_OdmItemRoot IF NOT EXISTS ON (n:OdmItemRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_OdmConditionRoot IF NOT EXISTS ON (n:OdmConditionRoot) ASSERT (n.uid) IS NODE KEY",
        "CREATE CONSTRAINT constraint_OdmFormalExpressionRoot IF NOT EXISTS ON (n:OdmFormalExpressionRoot) ASSERT (n.uid) IS NODE KEY",
    ]:
        session.write_transaction(run_querystring, querystring)

    print("\n-- Preloading TemplateParameter tree (Activity, Activity Group, Findings, Dose unit...) --")
    with session.begin_transaction() as tx:
        pre_load_template_parameter_tree(tx)

    session.write_transaction(lambda tx: tx.run("CREATE CONSTRAINT IF NOT EXISTS ON (c:Counter) ASSERT (c.counterId) IS NODE KEY"))

    print("\n-- Creating special query parameters (NA...) --")
    with session.begin_transaction() as tx:
        create_special_template_parameters(tx)

    session.close()

driver.close()
