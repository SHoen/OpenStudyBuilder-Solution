<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('Sidebar.study.study_criteria') }} ({{ studyId }})
    <help-button-with-panels :items="helpItems" />
  </div>
  <v-tabs v-model="tab">
    <v-tab
      v-for="type in criteriaTypes"
      :key="type.termUid"
      :href="`#${type.sponsorPreferredName}`"
      >
      {{ type.sponsorPreferredName }}
    </v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item
      v-for="type in criteriaTypes"
      :key="type.termUid"
      :id="type.sponsorPreferredName"
      >
      <eligibility-criteria-table
        :criteria-type="type"
        />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import { studySelectedNavigationGuard } from '@/mixins/studies'
import EligibilityCriteriaTable from '@/components/studies/EligibilityCriteriaTable'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'
import terms from '@/api/controlledTerminology/terms'

export default {
  mixins: [studySelectedNavigationGuard],
  components: {
    EligibilityCriteriaTable,
    HelpButtonWithPanels
  },
  data () {
    return {
      criteriaTypes: [],
      tab: null,
      helpItems: [
        'StudyCriteriaTable.general',
        'StudyCriteriaTable.study_criteria'
      ]
    }
  },
  mounted () {
    terms.getByCodelist('criteriaTypes').then(resp => {
      this.criteriaTypes = resp.data.items
    })
    this.tab = this.$route.params.tab
  },
  watch: {
    tab (newValue) {
      this.$router.push({
        name: 'StudySelectionCriteria',
        params: { tab: newValue }
      })
    }
  }
}
</script>

<style scoped>
.v-tabs-items {
  min-height: 50vh;
}
</style>
