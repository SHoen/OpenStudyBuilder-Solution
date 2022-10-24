<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('StudyRegistryIdentifiersView.title') }} ({{ studyId }})
    <help-button :help-text="$t('_help.RegistryIdentifiersTable.general')" />
  </div>
  <registry-identifiers-summary />
</div>
</template>

<script>
import { studySelectedNavigationGuard } from '@/mixins/studies'
import RegistryIdentifiersSummary from '@/components/studies/RegistryIdentifiersSummary'
import HelpButton from '@/components/tools/HelpButton'

export default {
  mixins: [studySelectedNavigationGuard],
  components: {
    RegistryIdentifiersSummary,
    HelpButton
  }
}
</script>
