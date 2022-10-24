<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('ObjectiveTemplatesView.title') }}
    <help-button :help-text="$t('_help.ObjectiveTemplatesTable.general')" />
  </div>
  <objective-template-table />
</div>
</template>

<script>
import ObjectiveTemplateTable from '@/components/library/ObjectiveTemplateTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    ObjectiveTemplateTable,
    HelpButton
  }
}
</script>
