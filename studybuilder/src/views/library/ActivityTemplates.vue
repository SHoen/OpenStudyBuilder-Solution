<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('ActivityTemplatesView.title') }}
    <help-button :help-text="$t('_help.ActivityTemplatesTable.general')" />
  </div>
  <activity-template-table />
</div>
</template>

<script>
import ActivityTemplateTable from '@/components/library/ActivityTemplateTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    ActivityTemplateTable,
    HelpButton
  }
}
</script>
