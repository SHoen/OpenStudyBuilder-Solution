import Vue from 'vue'
import VueRouter from 'vue-router'

import store from '@/store'

import Home from '../views/Home.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/library',
    name: 'Library',
    component: () => import('../views/library/Summary.vue'),
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
    path: '/library/ct_catalogues/:catalogueName/:codelistId',
    name: 'CodeListDetail',
    component: () => import('../views/library/CodeListDetail.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_catalogues/:catalogueName/:codelistId/terms/:termId',
    name: 'CodelistTermDetail',
    component: () => import('../views/library/CodelistTermDetail.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_catalogues/:catalogueName/:codelistId/terms',
    name: 'CodelistTerms',
    component: () => import('../views/library/CodelistTerms.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_catalogues/:catalogueName?',
    name: 'CtCatalogues',
    component: () => import('../views/library/CtCatalogues.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_packages/:catalogueName/history',
    name: 'CtPackagesHistory',
    component: () => import('../views/library/CtPackagesHistory.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_packages/:catalogueName/history/:codelistId',
    name: 'CtPackageCodelistHistory',
    component: () => import('../views/library/CtPackageCodelistHistory.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_packages/:catalogueName?/:packageName?',
    name: 'CtPackages',
    component: () => import('../views/library/CtPackages.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_packages/:catalogueName/:packageName/:codelistId/terms/:termId',
    name: 'CtPackageTermDetail',
    component: () => import('../views/library/CtPackageTermDetail.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ct_packages/:catalogueName/:packageName/:codelistId/terms',
    name: 'CtPackageTerms',
    component: () => import('../views/library/CtPackageTerms.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/cdisc',
    name: 'CDISC',
    component: () => import('../views/library/Cdisc.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/sponsor',
    name: 'Sponsor',
    component: () => import('../views/library/Sponsor.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/snomed',
    name: 'Snomed',
    component: () => import('../views/library/Snomed.vue'),
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
    component: () => import('../views/library/Unii.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/loinc',
    name: 'Loinc',
    component: () => import('../views/library/Loinc.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/ucum',
    name: 'Ucum',
    component: () => import('../views/library/Ucum.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/activities/:tab?',
    name: 'Activities',
    component: () => import('../views/library/Activities.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/units',
    name: 'Units',
    component: () => import('../views/library/Units.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/crfs/:tab?',
    name: 'Crfs',
    component: () => import('../views/library/Crfs.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/compounds/:tab?',
    name: 'Compounds',
    component: () => import('../views/library/Compounds.vue'),
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
    path: '/library/objective_templates',
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
    path: '/library/endpoint_templates',
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
    path: '/library/timeframe_templates',
    name: 'TimeframeTemplates',
    component: () => import('../views/library/TimeframeTemplates.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/activity_templates',
    name: 'ActivityTemplates',
    component: () => import('../views/library/ActivityTemplates.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/criteria_templates',
    name: 'CriteriaTemplates',
    component: () => import('../views/library/CriteriaTemplates.vue'),
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
    component: () => import('../views/library/Cdash.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/sdtm',
    name: 'Sdtm',
    component: () => import('../views/library/Sdtm.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/library/adam',
    name: 'Adam',
    component: () => import('../views/library/Adam.vue'),
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
    component: () => import('../views/library/Objectives.vue'),
    meta: {
      documentation: { page: 'userguide/library/template_instatiations/objectives.html' },
      authRequired: true
    }
  },
  {
    path: '/library/endpoints',
    name: 'Endpoints',
    component: () => import('../views/library/Endpoints.vue'),
    meta: {
      documentation: { page: 'userguide/library/template_instatiations/endpoints.html' },
      authRequired: true
    }
  },
  {
    path: '/library/timeframe_instances',
    name: 'Timeframes',
    component: () => import('../views/library/Timeframes.vue'),
    meta: {
      documentation: { page: 'userguide/library/template_instatiations/timeframes.html' },
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
    path: '/studies',
    name: 'Studies',
    component: () => import('../views/studies/Summary.vue'),
    meta: {
      resetBreadcrumbs: true,
      authRequired: true
    }
  },
  {
    path: '/studies/study_status',
    name: 'StudyStatus',
    component: () => import('../views/studies/StudyStatus.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/specification_dashboard',
    name: 'SpecificationDashboard',
    component: () => import('../views/studies/SpecificationDashboard.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/study_title',
    name: 'StudyTitle',
    component: () => import('../views/studies/StudyTitle.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/select_or_add_study',
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
    path: '/studies/study_purpose/:tab?',
    name: 'StudyPurpose',
    component: () => import('../views/studies/StudyPurpose.vue'),
    meta: {
      authRequired: true,
      studyRequired: true
    }
  },
  {
    path: '/studies/activities/:tab?',
    name: 'StudyActivities',
    component: () => import('../views/studies/Activities.vue'),
    meta: {
      authRequired: true,
      studyRequired: true
    }
  },
  {
    path: '/studies/selection_criteria/:tab?',
    name: 'StudySelectionCriteria',
    component: () => import('../views/studies/StudyCriteria.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/study_interventions/:tab?',
    name: 'StudyInterventions',
    component: () => import('../views/studies/Interventions.vue'),
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
    path: '/studies/protocol_elements',
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
    path: '/studies/study_properties/:tab?',
    name: 'StudyProperties',
    component: () => import('../views/studies/StudyProperties.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/study_structure/:tab?',
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
    path: '/studies/sdtm_specification',
    name: 'SdtmSpecification',
    component: () => import('../views/studies/SdtmSpecification.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/pharma_cm_specifications',
    name: 'PharmaCmSpecifications',
    component: () => import('../views/studies/PharmaCmSpecifications.vue'),
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
    component: () => import('../views/studies/Terminology.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/studies/registry_identifiers',
    name: 'StudyRegistryIdentifiers',
    component: () => import('../views/studies/RegistryIdentifiers.vue'),
    meta: {
      studyRequired: true,
      authRequired: true
    }
  },
  {
    path: '/studies/population',
    name: 'StudyPopulation',
    component: () => import('../views/studies/Population.vue'),
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
    path: '/studies/analysis_study_metadata_new',
    name: 'AnalysisStudyMetadataNew',
    component: () => import('../views/studies/AnalysisStudyMetadataNew.vue'),
    meta: {
      authRequired: true
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
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      layoutTemplate: 'empty'
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: {
      authRequired: true
    }
  },
  {
    path: '/oauth-callback',
    component: () => import('../views/AuthCallback.vue'),
    meta: {
      layoutTemplate: 'error'
    }
  },
  {
    path: '/logout',
    name: 'Logout',
    component: () => import('../views/Logout.vue')
  },
  {
    path: '*',
    name: 'NotFound',
    component: () => import('../views/404.vue')
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

router.beforeEach((to, from, next) => {
  if (Vue.prototype.$config.AUTH_ENABLED === '1' && to.matched.some(record => record.meta.authRequired)) {
    Vue.prototype.$auth.validateAccess(to, from, next)
  } else {
    next()
  }
})

router.beforeEach((to, from, next) => {
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
    if (section) {
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
