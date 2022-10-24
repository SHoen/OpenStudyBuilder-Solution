<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('Sidebar.study.study_properties') }} ({{ studyId }})
    <help-button-with-panels
      :help-text="$t('_help.StudyProperties.general')"
      :items="helpItems"
      />
  </div>
  <v-tabs v-model="tab">
    <v-tab href="#type">{{ $t('Sidebar.study.study_type') }}</v-tab>
    <v-tab href="#attributes">{{ $t('Sidebar.study.study_attributes') }}</v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item id="type">
      <study-type-summary />
    </v-tab-item>
    <v-tab-item id="attributes">
      <intervention-type-summary />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'
import InterventionTypeSummary from '@/components/studies/InterventionTypeSummary'
import { studySelectedNavigationGuard } from '@/mixins/studies'
import StudyTypeSummary from '@/components/studies/StudyTypeSummary'

export default {
  mixins: [studySelectedNavigationGuard],
  components: {
    InterventionTypeSummary,
    HelpButtonWithPanels,
    StudyTypeSummary
  },
  data () {
    return {
      helpItems: [
        'StudyProperties.study_type'
      ],
      tab: null
    }
  },
  mounted () {
    this.tab = this.$route.params.tab
  },
  watch: {
    tab (newValue) {
      this.$router.push({
        name: 'StudyProperties',
        params: { tab: newValue }
      })
    }
  }
}
</script>
