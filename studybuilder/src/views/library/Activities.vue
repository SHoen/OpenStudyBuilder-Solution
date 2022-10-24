<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('Sidebar.library.activities') }}
    <help-button :help-text="$t('_help.ActivitiesTable.general')" />
  </div>
   <v-tabs v-model="tab">
    <v-tab href="#activities">{{ $t('ActivityTable.activities') }}</v-tab>
    <v-tab href="#activity-groups">{{ $t('ActivityTable.activities_overview') }}</v-tab>
    <v-tab href="#activity-instances">{{ $t('ActivityTable.instances') }}</v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item id="activities">
      <activities-table
        source="activities"/>
    </v-tab-item>
    <v-tab-item id="activity-groups">
      <activities-table
        source="activity-groups"/>
    </v-tab-item>
    <v-tab-item id="activity-instances">
      <activities-table
        source="activity-instances"/>
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import ActivitiesTable from '@/components/library/ActivitiesTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    ActivitiesTable,
    HelpButton
  },
  data () {
    return {
      tab: 0
    }
  },
  mounted () {
    this.tab = this.$route.params.tab
  },
  watch: {
    tab (newValue) {
      this.$router.push({
        name: 'Activities',
        params: { tab: newValue }
      })
    }
  }
}
</script>
