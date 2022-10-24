<template>
<div>
  <v-tabs v-model="tab">
    <v-tab href="#tab-0">{{ $t('Sidebar.study.blank_crf') }}</v-tab>
    <v-tab href="#tab-1">{{ $t('Sidebar.study.cdash_crf') }}</v-tab>
    <v-tab href="#tab-2">{{ $t('Sidebar.study.sdtm_crf') }}</v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item id="tab-0">
      <UnderConstruction />
    </v-tab-item>
    <v-tab-item id="tab-1">
       <UnderConstruction />
    </v-tab-item>
     <v-tab-item id="tab-2">
       <UnderConstruction />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import UnderConstruction from '../../components/layout/UnderConstruction.vue'

export default {
  components: {

    UnderConstruction
  },
  data () {
    return {
      tab: null
    }
  },
  mounted () {
    this.tab = localStorage.getItem('templatesTab') || 'tab-0'
  },
  watch: {
    tab (value) {
      localStorage.setItem('templatesTab', value)
    }
  }
}
</script>
