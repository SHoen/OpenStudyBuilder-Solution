<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('EndpointsView.title') }}
    <help-button :help-text="$t('_help.EndpointsTable.general')" />
  </div>
  <endpoint-table />
</div>
</template>

<script>
import EndpointTable from '@/components/library/EndpointTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    EndpointTable,
    HelpButton
  }
}
</script>
