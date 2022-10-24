<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('TimeframesView.title') }}
    <help-button :help-text="$t('_help.TimeframesTable.general')" />
  </div>
  <timeframe-table />
</div>
</template>

<script>
import TimeframeTable from '@/components/library/TimeframeTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    TimeframeTable,
    HelpButton
  },
  data () {
    return {
      tab: null
    }
  }
}
</script>
