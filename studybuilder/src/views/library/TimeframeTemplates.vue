<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('TimeframeTemplatesView.title') }}
    <help-button :help-text="$t('_help.TimeframeTemplatesTable.general')" />
  </div>
  <timeframe-template-table />
</div>
</template>

<script>
import TimeframeTemplateTable from '@/components/library/TimeframeTemplateTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    TimeframeTemplateTable,
    HelpButton
  }
}
</script>
