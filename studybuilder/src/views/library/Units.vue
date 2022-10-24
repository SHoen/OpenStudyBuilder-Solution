<template>
<div class="px-4">
  <div class="d-flex page-title">{{ $t('UnitsView.title') }} <help-button :title="$t('_global.definition')" :help-text="$t('HelpMessages.units')" /></div>
  <unit-table />
</div>
</template>

<script>
import HelpButton from '@/components/tools/HelpButton'
import UnitTable from '@/components/library/UnitTable'

export default {
  components: {
    HelpButton,
    UnitTable
  }
}
</script>
