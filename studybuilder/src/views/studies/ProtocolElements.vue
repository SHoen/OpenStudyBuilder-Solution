<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('StudyProtocolElementsView.title') }} ({{ studyId }})
    <help-button :help-text="$t('_help.ProtocolElementsTable.general')" />
  </div>
  <v-tabs v-model="tab">
    <v-tab href="#tab-0">{{ $t('Sidebar.study.protocol_title') }}</v-tab>
    <v-tab href="#tab-1">{{ $t('Sidebar.study.flow_chart') }}</v-tab>
    <v-tab href="#tab-2">{{ $t('Sidebar.study.objective_endpoints_estimands') }}</v-tab>
    <v-tab href="#tab-3">{{ $t('Sidebar.study.study_design') }}</v-tab>
    <v-tab href="#tab-4">{{ $t('Sidebar.study.study_population') }}</v-tab>
    <v-tab href="#tab-5">{{ $t('Sidebar.study.study_interventions_and_therapy') }}</v-tab>
    <v-tab href="#tab-6">{{ $t('Sidebar.study.study_activities') }}</v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item id="tab-0">
      <protocol-title-page />
    </v-tab-item>
    <v-tab-item id="tab-1">
      <protocol-flowchart :study-uid="selectedStudy.uid"  :update="updateProtocol" />
    </v-tab-item>
    <v-tab-item id="tab-2">
      <protocol-elements-objective-table />
    </v-tab-item>
     <v-tab-item id="tab-3">
       <protocol-elements-study-design :study-uid="selectedStudy.uid" :update="updateDesign"/>
    </v-tab-item>
     <v-tab-item id="tab-4">
       <protocol-elements-study-population-summary />
    </v-tab-item>
     <v-tab-item id="tab-5">
       <protocol-elements-study-interventions :study-uid="selectedStudy.uid" :update="updateInterventions"/>
    </v-tab-item>
     <v-tab-item id="tab-6">
       <protocol-elements-procedures-and-activities />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import { studySelectedNavigationGuard } from '@/mixins/studies'
import ProtocolElementsObjectiveTable from '@/components/studies/ProtocolElementsObjectiveTable'
import ProtocolElementsStudyPopulationSummary from '@/components/studies/ProtocolElementsStudyPopulationSummary'
import ProtocolElementsStudyDesign from '@/components/studies/ProtocolElementsStudyDesign'
import ProtocolElementsStudyInterventions from '@/components/studies/ProtocolElementsStudyIntervention'
import ProtocolElementsProceduresAndActivities from '@/components/studies/ProtocolElementsProceduresAndActivities'
import ProtocolFlowchart from '@/components/studies/ProtocolFlowchart'
import ProtocolTitlePage from '@/components/studies/ProtocolTitlePage'
import HelpButton from '@/components/tools/HelpButton'

export default {
  mixins: [studySelectedNavigationGuard],
  components: {
    ProtocolElementsObjectiveTable,
    ProtocolFlowchart,
    HelpButton,
    ProtocolTitlePage,
    ProtocolElementsStudyPopulationSummary,
    ProtocolElementsStudyDesign,
    ProtocolElementsStudyInterventions,
    ProtocolElementsProceduresAndActivities
  },
  data () {
    return {
      tab: null,
      updateProtocol: 0,
      updateDesign: 0,
      updateInterventions: 0
    }
  },
  mounted () {
    this.tab = localStorage.getItem('templatesTab') || 'tab-0'
  },
  watch: {
    tab (value) {
      localStorage.setItem('templatesTab', value)
      switch (value) {
        case 'tab-1':
          this.updateProtocol++
          break
        case 'tab-3':
          this.updateDesign++
          break
        case 'tab-5':
          this.updateInterventions++
          break
      }
    }
  }
}
</script>
