<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('StudyManageView.title') }}
    <help-button :help-text="$t('_help.SelectOrAddStudyTable.general')" />
  </div>
  <study-table />
</div>
</template>

<script>
import StudyTable from '@/components/studies/StudyTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    StudyTable,
    HelpButton
  }
}
</script>
