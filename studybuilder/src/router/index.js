import Vue from 'vue'
import VueRouter from 'vue-router'

import store from '@/store'
import study from '@/api/study'

Vue.use(VueRouter)

const routes = [
  {
    path: '/library',
    name: 'Library',
    component: () => import('../views/library/SummaryPage.vue'),
    meta: {
      resetBreadcrumbs: true,
      authRequired: true
    }
  },
  {
    path: '/library/dashboard',
    name: 'LibraryDashboard',
    component: () => import('../views/library/LibraryDashboard.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_dashboard',
    name: 'CTDashboard',
    component: () => import('../views/library/CTDashboard.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_catalogues/:catalogue_name/:codelist_id',
    name: 'CodeListDetail',
    component: () => import('../views/library/CodeListDetail.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_catalogues/:catalogue_name/:codelist_id/terms/:term_id',
    name: 'CodelistTermDetail',
    component: () => import('../views/library/CodelistTermDetail.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_catalogues/:catalogue_name/:codelist_id/terms',
    name: 'CodelistTerms',
    component: () => import('../views/library/CodelistTerms.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_catalogues/:catalogue_name?',
    name: 'CtCatalogues',
    component: () => import('../views/library/CtCatalogues.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_packages/:catalogue_name/history',
    name: 'CtPackagesHistory',
    component: () => import('../views/library/CtPackagesHistory.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_packages/:catalogue_name/history/:codelist_id',
    name: 'CtPackageCodelistHistory',
    component: () => import('../views/library/CtPackageCodelistHistory.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_packages/:catalogue_name?/:package_name?',
    name: 'CtPackages',
    component: () => import('../views/library/CtPackages.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_packages/:catalogue_name/:package_name/:codelist_id/terms/:term_id',
    name: 'CtPackageTermDetail',
    component: () => import('../views/library/CtPackageTermDetail.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_packages/:catalogue_name/:package_name/:codelist_id/terms',
    name: 'CtPackageTerms',
    component: () => import('../views/library/CtPackageTerms.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/cdisc',
    name: 'CDISC',
    component: () => import('../views/library/CdiscPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/sponsor',
    name: 'Sponsor',
    component: () => import('../views/library/SponsorPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/snomed',
    name: 'Snomed',
    component: () => import('../views/library/SnomedPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/meddra',
    name: 'MedDra',
    component: () => import('../views/library/MedDra.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/medrt',
    name: 'MedRt',
    component: () => import('../views/library/MedRt.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/unii',
    name: 'Unii',
    component: () => import('../views/library/UniiPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/loinc',
    name: 'Loinc',
    component: () => import('../views/library/LoincPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ucum',
    name: 'Ucum',
    component: () => import('../views/library/UcumPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/activities/activities/:id/overview',
    name: 'ActivityOverview',
    component: () => import('../views/library/ActivityOverview.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/activities/activity-instances/:id/overview',
    name: 'ActivityInstanceOverview',
    component: () => import('../views/library/ActivityInstanceOverview.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/activities/:tab?',
    name: 'Activities',
    component: () => import('../views/library/ActivitiesPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/units',
    name: 'Units',
    component: () => import('../views/library/UnitsPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/crfs/:tab?/:type?/:uid?',
    name: 'Crfs',
    component: () => import('../views/library/CrfsPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/compounds/:tab?',
    name: 'Compounds',
    component: () => import('../views/library/CompoundsPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/compound/:id',
    name: 'CompoundOverview',
    component: () => import('../views/library/CompoundOverview.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/objective_templates/:tab?',
    name: 'ObjectiveTemplates',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import('../views/library/ObjectiveTemplates.vue'),
    meta: {
      documentation: { page: 'userguide/library/objectivestemplates.html' },
      authRequired: true
    }
  },
  {
    path: '/library/endpoint_templates/:tab?',
    name: 'EndpointTemplates',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import('../views/library/EndpointTemplates.vue'),
    meta: {
      documentation: { page: 'userguide/library/endpointstemplates.html' },
      authRequired: true
    }
  },
  {
    path: '/library/timeframe_templates/:tab?',
    name: 'TimeframeTemplates',
    component: () => import('../views/library/TimeframeTemplates.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/activity_templates/:tab?',
    name: 'ActivityTemplates',
    component: () => import('../views/library/ActivityTemplates.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/criteria_templates/:type?/:tab?',
    name: 'CriteriaTemplates',
    component: () => import('../views/library/CriteriaTemplates.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/footnote_templates/:tab?',
    name: 'FootnoteTemplates',
    component: () => import('../views/library/FootnoteTemplates.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/project_templates',
    name: 'ProjectTemplates',
    component: () => import('../views/library/ProjectTemplates.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/shared_templates',
    name: 'SharedTemplates',
    component: () => import('../views/library/SharedTemplates.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/supporting_templates',
    name: 'SupportingTemplates',
    component: () => import('../views/library/SupportingTemplates.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/cdash',
    name: 'Cdash',
    component: () => import('../views/library/CdashPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/sdtm',
    name: 'Sdtm',
    component: () => import('../views/library/SdtmPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/adam',
    name: 'Adam',
    component: () => import('../views/library/AdamPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/general_clinical_metadata',
    name: 'GeneralClinicalMetadata',
    component: () => import('../views/library/GeneralClinicalMetadata.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/cdash_standards',
    name: 'CdashStandards',
    component: () => import('../views/library/CdashStandards.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/sdtm_standards_dmw',
    name: 'SdtmStdDmw',
    component: () => import('../views/library/SdtmStdDmw.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/adam_standards_cst',
    name: 'AdamStdCst',
    component: () => import('../views/library/AdamStdCst.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/adam_standards_new',
    name: 'AdamStdNew',
    component: () => import('../views/library/AdamStdNew.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/sdtm_standards_cst',
    name: 'SdtmStdCst',
    component: () => import('../views/library/SdtmStdCst.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/objectives',
    name: 'Objectives',
    component: () => import('../views/library/ObjectivesPage.vue'),
    meta: {
      documentation: { page: 'userguide/library/template_instatiations/objectives.html' },
      authRequired: true
    }
  },
  {
    path: '/library/endpoints',
    name: 'Endpoints',
    component: () => import('../views/library/EndpointsPage.vue'),
    meta: {
      documentation: { page: 'userguide/library/template_instatiations/endpoints.html' },
      authRequired: true
    }
  },
  {
    path: '/library/timeframe_instances',
    name: 'Timeframes',
    component: () => import('../views/library/TimeframesPage.vue'),
    meta: {
      documentation: { page: 'userguide/library/template_instatiations/timeframes.html' },
      authRequired: true
    }
  },
  {
    path: '/library/activity_instruction_instances',
    name: 'ActivityInstructions',
    component: () => import('../views/library/ActivityInstructions.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/criteria_instances',
    name: 'CriteriaInstances',
    component: () => import('../views/library/CriteriaInstances.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/footnote_instances',
    name: 'FootnoteInstances',
    component: () => import('../views/library/FootnotesPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/process_overview',
    name: 'ProcessOverview',
    component: () => import('../views/library/ProcessOverview.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/clinical_programmes',
    name: 'ClinicalProgrammes',
    component: () => import('../views/library/ClinicalProgrammeList.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/projects',
    name: 'Projects',
    component: () => import('../views/library/ProjectList.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies',
    name: 'Studies',
    component: () => import('../views/studies/SummaryPage.vue'),
    meta: {
      resetBreadcrumbs: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_status/:tab?',
    name: 'StudyStatus',
    component: () => import('../views/studies/StudyStatus.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/specification_dashboard',
    name: 'SpecificationDashboard',
    component: () => import('../views/studies/SpecificationDashboard.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_title',
    name: 'StudyTitle',
    component: () => import('../views/studies/StudyTitle.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/select_or_add_study/:tab?',
    name: 'SelectOrAddStudy',
    component: () => import('../views/studies/SelectOrAddStudy.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/project_standards',
    name: 'ProjectStandards',
    component: () => import('../views/studies/ProjectStandards.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_purpose/:tab?',
    name: 'StudyPurpose',
    component: () => import('../views/studies/StudyPurpose.vue'),
    meta: {
      authRequired: true,
      studyRequired: true
    }
  },
  {
    path: '/studies/:study_id/activities/:tab?',
    name: 'StudyActivities',
    component: () => import('../views/studies/ActivitiesPage.vue'),
    meta: {
      authRequired: true,
      studyRequired: true
    }
  },
  {
    path: '/studies/:study_id/selection_criteria/:tab?',
    name: 'StudySelectionCriteria',
    component: () => import('../views/studies/StudyCriteria.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_interventions/:tab?',
    name: 'StudyInterventions',
    component: () => import('../views/studies/InterventionsPage.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/standardisation_plan',
    name: 'StandardisationPlan',
    component: () => import('../views/studies/StandardisationPlan.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/protocol_elements',
    name: 'ProtocolElements',
    component: () => import('../views/studies/ProtocolElements.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/objective_endpoints_estimands',
    name: 'ObjectiveEndpointsAndEstimands',
    component: () => import('../views/studies/ObjectiveEndpointsAndEstimands.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_properties/:tab?',
    name: 'StudyProperties',
    component: () => import('../views/studies/StudyProperties.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_structure/:tab?',
    name: 'StudyStructure',
    component: () => import('../views/studies/StudyStructure.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/crf_specifications',
    name: 'CrfSpecifications',
    component: () => import('../views/studies/CrfSpecifications.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/blank_crf',
    name: 'BlankCrf',
    component: () => import('../views/studies/BlankCrf.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/cdash_crf',
    name: 'CdashAnnotatedCrf',
    component: () => import('../views/studies/CdashAnnotatedCrf.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/sdtm_crf',
    name: 'SdtmAnnotatedCrf',
    component: () => import('../views/studies/SdtmAnnotatedCrf.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/odm_specification',
    name: 'OdmSpecification',
    component: () => import('../views/studies/OdmSpecification.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/ctr_odm_xml',
    name: 'CtrOdmXml',
    component: () => import('../views/studies/CtrOdmXml.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/sdtm_specification',
    name: 'SdtmSpecification',
    component: () => import('../views/studies/SdtmSpecification.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/study_disclosure',
    name: 'StudyDisclosure',
    component: () => import('../views/studies/StudyDisclosure.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/trial_supplies_specifications',
    name: 'TrialSuppliesSpecifications',
    component: () => import('../views/studies/TrialSuppliesSpecifications.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/sdtm_study_design_datasets',
    name: 'SdtmStudyDesignDatasets',
    component: () => import('../views/studies/SdtmStudyDesignDatasets.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/adam_specification',
    name: 'AdamSpecification',
    component: () => import('../views/studies/AdamSpecification.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/terminology',
    name: 'StudyTerminology',
    component: () => import('../views/studies/TerminologyPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/registry_identifiers',
    name: 'StudyRegistryIdentifiers',
    component: () => import('../views/studies/RegistryIdentifiers.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/population',
    name: 'StudyPopulation',
    component: () => import('../views/studies/PopulationPage.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/adam_define_cst',
    name: 'AdamDefineCst',
    component: () => import('../views/studies/AdamDefineCst.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/adam_define_p21',
    name: 'AdamDefineP21',
    component: () => import('../views/studies/AdamDefineP21.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/analysis_study_metadata_new/:tab?',
    name: 'AnalysisStudyMetadataNew',
    component: () => import('../views/studies/AnalysisStudyMetadataNew.vue'),
    meta: {
      authRequired: true,
      studyRequired: true
    }
  },
  {
    path: '/studies/dmw_additional_metadata',
    name: 'DmwAdditionalMetadata',
    component: () => import('../views/studies/DmwAdditionalMetadata.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/mma_trial_metadata',
    name: 'MmaTrialMetadata',
    component: () => import('../views/studies/MmaTrialMetadata.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/sdtm_additional_metadata',
    name: 'SdtmAdditionalMetadata',
    component: () => import('../views/studies/SdtmAdditionalMetadata.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/sdtm_define_p21',
    name: 'SdtmDefineP21',
    component: () => import('../views/studies/SdtmDefineCst.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/sdtm_define_cst',
    name: 'SdtmDefineCst',
    component: () => import('../views/studies/SdtmDefineP21.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/protocol_process',
    name: 'ProtocolProcess',
    component: () => import('../views/studies/ProtocolProcess.vue')
  },
  {
    path: '/studies/:study_id/study_structure/arms/:id/overview',
    name: 'StudyArmOverview',
    component: () => import('../components/studies/overviews/StudyArmOverview.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_structure/branches/:id/overview',
    name: 'StudyBranchArmOverview',
    component: () => import('../components/studies/overviews/StudyBranchArmOverview.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_structure/cohorts/:id/overview',
    name: 'StudyCohortOverview',
    component: () => import('../components/studies/overviews/StudyCohortOverview.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_structure/epochs/:id/overview',
    name: 'StudyEpochOverview',
    component: () => import('../components/studies/overviews/StudyEpochOverview.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_structure/elements/:id/overview',
    name: 'StudyElementOverview',
    component: () => import('../components/studies/overviews/StudyElementOverview.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_structure/visits/:id/overview',
    name: 'StudyVisitOverview',
    component: () => import('../components/studies/overviews/StudyVisitOverview.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/activities/list/:id/overview',
    name: 'StudyActivityOverview',
    component: () => import('../components/studies/overviews/StudyActivityOverview.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/:study_id/study_interventions/study_compounds/:id/overview',
    name: 'StudyCompoundOverview',
    component: () => import('../components/studies/overviews/StudyCompoundOverview.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomePage.vue'),
    meta: {
      layoutTemplate: 'empty'
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginPage.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/oauth-callback',
    name: 'AuthCallback',
    component: () => import('../views/AuthCallback.vue'),
    meta: {
      layoutTemplate: 'error'
    }
  },
  {
    path: '/logout',
    name: 'Logout',
    component: () => import('../views/LogoutPage.vue'),
    meta: {}
  }
]

const { isNavigationFailure, NavigationFailureType } = VueRouter
const originalPush = VueRouter.prototype.push
VueRouter.prototype.push = function push (location) {
  return originalPush.call(this, location).catch((error) => {
    if (NavigationFailureType && !isNavigationFailure(error, NavigationFailureType.duplicated)) {
      throw Error(error)
    }
  })
}

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

async function saveStudyUid (studyUid) {
  const currentlySelectedStudy = JSON.parse(localStorage.getItem('selectedStudy'))
  if (!currentlySelectedStudy || (currentlySelectedStudy && currentlySelectedStudy.uid !== studyUid)) {
    try {
      const resp = await study.getStudy(studyUid)
      store.commit('studiesGeneral/SELECT_STUDY', { studyObj: resp.data })
    } catch (_err) {
      store.commit('studiesGeneral/UNSELECT_STUDY')
      store.studyId = null
      router.push('/studies')
    }
  }
}

router.beforeEach(async (to, from, next) => {
  if (to.params.study_id && to.params.study_id !== '*') {
    await saveStudyUid(to.params.study_id)
  }

  if (Vue.prototype.$config.OAUTH_ENABLED && to.matched.some(record => record.meta.authRequired)) {
    Vue.prototype.$auth.validateAccess(to, from, next)
  }

  next()
})

router.onError(error => {
  // In case of 'Loading chunk x failed' error, reload the page once
  if (/loading chunk \d* failed./i.test(error.message)) {
    if (window.location.hash !== 'reloaded') {
      window.location.hash = 'reloaded'
      window.location.reload()
    }
  }
})

router.beforeEach(async (to, from, next) => {
  if (to.matched.some(record => record.meta.documentation)) {
    let urlPath = `${to.meta.documentation.page}`
    if (to.meta.documentation.anchor) {
      urlPath += `#${to.meta.documentation.anchor}`
    }
    store.commit('app/SET_HELP_PATH', urlPath)
  }
  if (to.matched.some(record => record.meta.resetBreadcrumbs)) {
    store.commit('app/RESET_BREADCRUMBS')
    store.commit('app/SET_SECTION', to.name)
  }
  if (to.path !== '/' && to.path !== '/oauth-callback' && !store.getters['app/section']) {
    /* We are probably doing a full refresh of the page, let's guess
     * the breadcrumbs based on current url */
    const basePath = '/' + to.path.split('/')[1]
    const baseRoute = router.resolve(basePath)
    const section = baseRoute.route.name
    if (section && section !== 'Logout') {
      store.commit('app/SET_SECTION', section)
      const currentRoute = router.resolve(to.path)
      for (const item of store.getters['app/menuItems'][section].items) {
        if (item.children) {
          let found = false
          for (const subitem of item.children) {
            if (subitem.url.name === currentRoute.route.name) {
              store.dispatch('app/addBreadcrumbsLevel', { text: item.title, to: item.url, index: 1 })
              store.dispatch('app/addBreadcrumbsLevel', { text: subitem.title, to: subitem.url })
              found = true
              break
            }
          }
          if (found) {
            break
          }
        } else {
          if (item.url.name === currentRoute.name) {
            store.dispatch('app/addBreadcrumbsLevel', { text: item.title, to: item.url, index: 1 })
            break
          }
        }
      }
    }
  }
  next()
})

export default router
