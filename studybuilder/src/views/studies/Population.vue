<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('StudyPopulationView.title') }} ({{ studyId }})
    <help-button :help-text="$t('_help.StudyPopulationTable.general')" />
  </div>
  <study-population-summary />
</div>
</template>

<script>
import { studySelectedNavigationGuard } from '@/mixins/studies'
import StudyPopulationSummary from '@/components/studies/StudyPopulationSummary'
import HelpButton from '@/components/tools/HelpButton'

export default {
  mixins: [studySelectedNavigationGuard],
  components: {
    StudyPopulationSummary,
    HelpButton
  }
}
</script>
