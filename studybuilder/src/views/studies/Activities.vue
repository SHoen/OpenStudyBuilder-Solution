<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('ActivitiesView.title') }} ({{ studyId }})
  </div>
  <v-tabs v-model="tab">
    <v-tab href="#list">{{ $t('ActivitiesView.tab1_title') }}</v-tab>
    <v-tab href="#detailed">{{ $t('ActivitiesView.tab2_title') }}</v-tab>
    <v-tab href="#protocol">{{ $t('ActivitiesView.tab3_title') }}</v-tab>
    <v-tab href="#instructions">{{ $t('ActivitiesView.tab4_title') }}</v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item id="list">
      <study-activity-table
        />
    </v-tab-item>
    <v-tab-item id="detailed">
      <detailed-flowchart
        :update="updateFlowchart"/>
    </v-tab-item>
    <v-tab-item id="protocol">
      <protocol-flowchart :study-uid="selectedStudy.uid" :update="updateProtocol" />
    </v-tab-item>
    <v-tab-item id="instructions">
      <study-activity-instruction-table />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import DetailedFlowchart from '@/components/studies/DetailedFlowchart'
import ProtocolFlowchart from '@/components/studies/ProtocolFlowchart'
import StudyActivityInstructionTable from '@/components/studies/StudyActivityInstructionTable'
import StudyActivityTable from '@/components/studies/StudyActivityTable'
import { studySelectedNavigationGuard } from '@/mixins/studies'

export default {
  mixins: [studySelectedNavigationGuard],
  components: {
    DetailedFlowchart,
    ProtocolFlowchart,
    StudyActivityInstructionTable,
    StudyActivityTable
  },
  data () {
    return {
      tab: null,
      updateProtocol: 0,
      updateFlowchart: 0
    }
  },
  mounted () {
    this.tab = this.$route.params.tab
  },
  watch: {
    tab (newValue) {
      this.$router.push({
        name: 'StudyActivities',
        params: { tab: newValue }
      })
      if (newValue === 'protocol') this.updateProtocol++
      if (newValue === 'detailed') this.updateFlowchart++
    },
    /*
    ** Non optimal way to allow direct links (ie. a tags with href set to a tab url)
    ** It could create a loop with the above watcher but it works because routes are the same
    ** eventually.
    */
    '$route.params.tab' (newValue) {
      this.tab = newValue
    }
  }
}
</script>
