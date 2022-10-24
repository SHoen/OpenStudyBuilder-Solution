<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('EndpointTemplatesView.title') }}
    <help-button :help-text="$t('_help.EndpointTemplatesTable.general')" />
  </div>
  <endpoint-template-table />
</div>
</template>

<script>
import EndpointTemplateTable from '@/components/library/EndpointTemplateTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    EndpointTemplateTable,
    HelpButton
  }
}
</script>
