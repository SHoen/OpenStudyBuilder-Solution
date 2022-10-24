<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('Sidebar.study.purpose') }} ({{ studyId }})
    <help-button-with-panels
      :help-text="$t('_help.StudyPurposeView.general')"
      :items="helpItems"
      />
  </div>
  <v-tabs v-model="tab">
    <v-tab href="#objectives">{{ $t('StudyPurposeView.study_objectives') }}</v-tab>
    <v-tab href="#endpoints">{{ $t('StudyPurposeView.study_endpoints') }}</v-tab>
    <v-tab href="#estimands">{{ $t('StudyPurposeView.study_estimands') }}</v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item id="objectives">
      <objective-table
        @updated="endpointTableKey++"
        />
    </v-tab-item>
    <v-tab-item id="endpoints">
      <endpoint-table
        :key="endpointTableKey"
        />
    </v-tab-item>
    <v-tab-item id="estimands">
      <UnderConstruction />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import { studySelectedNavigationGuard } from '@/mixins/studies'
import EndpointTable from '@/components/studies/EndpointTable'
import ObjectiveTable from '@/components/studies/ObjectiveTable'
import UnderConstruction from '@/components/layout/UnderConstruction.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'

export default {
  mixins: [studySelectedNavigationGuard],
  components: {
    EndpointTable,
    HelpButtonWithPanels,
    ObjectiveTable,
    UnderConstruction
  },
  data () {
    return {
      endpointTableKey: 1,
      tab: null,
      helpItems: [
        'StudyPurposeView.study_objectives',
        'StudyPurposeView.study_endpoints',
        'StudyPurposeView.study_estimands'
      ]
    }
  },
  mounted () {
    this.tab = this.$route.params.tab
  },
  watch: {
    tab (newValue) {
      this.$router.push({
        name: 'StudyPurpose',
        params: { tab: newValue }
      })
      this.helpItems.splice(3, 4)
      if (newValue === 'objectives') {
        this.helpItems.push(
          'StudyObjectivesTable.objective_level',
          'StudyObjectivesTable.endpoint_count',
          'StudyObjectivesTable.objective'
        )
      } else if (newValue === 'endpoints') {
        this.helpItems.push(
          'StudyEndpointsTable.endpoint_title',
          'StudyEndpointsTable.objective',
          'StudyEndpointsTable.time_frame',
          'StudyEndpointsTable.units'
        )
      }
    }
  }
}
</script>
