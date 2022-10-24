<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('ObjectivesView.title') }}
    <help-button :help-text="$t('_help.ObjectivesTable.general')" />
  </div>
  <objective-table />
</div>
</template>

<script>
import ObjectiveTable from '@/components/library/ObjectiveTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    ObjectiveTable,
    HelpButton
  }
}
</script>
