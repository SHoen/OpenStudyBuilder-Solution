<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('SdtmSpecificationsView.title') }}
    <help-button :help-text="$t('_help.SdtmSpecificationTable.general')" />
  </div>
  <v-tabs v-model="tab">
    <v-tab href="#tab-0">{{ $t('SdtmDesignTable.trial_arm') }}</v-tab>
    <v-tab href="#tab-1">{{ $t('SdtmDesignTable.trial_elem') }}</v-tab>
    <v-tab href="#tab-2">{{ $t('SdtmDesignTable.trial_visits') }}</v-tab>
    <v-tab href="#tab-3">{{ $t('SdtmDesignTable.trial_incl_excl') }}</v-tab>
    <v-tab href="#tab-4">{{ $t('SdtmDesignTable.trial_disease') }}</v-tab>
    <v-tab href="#tab-5">{{ $t('SdtmDesignTable.trial_summary') }}</v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item id="tab-0">
      <sdtm-design-table type="TA"/>
    </v-tab-item>
    <v-tab-item id="tab-1">
      <sdtm-design-table type="TE"/>
    </v-tab-item>
    <v-tab-item id="tab-2">
      <sdtm-design-table type="TV"/>
    </v-tab-item>
    <v-tab-item id="tab-3">
      <sdtm-design-table type="TI"/>
    </v-tab-item>
    <v-tab-item id="tab-4">
      <UnderConstruction />
    </v-tab-item>
    <v-tab-item id="tab-5">
      <sdtm-design-table type="TS"/>
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import SdtmDesignTable from '@/components/studies/SdtmDesignTable'
import UnderConstruction from '@/components/layout/UnderConstruction.vue'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    SdtmDesignTable,
    UnderConstruction,
    HelpButton
  },
  data () {
    return {
      tab: null
    }
  }
}
</script>
