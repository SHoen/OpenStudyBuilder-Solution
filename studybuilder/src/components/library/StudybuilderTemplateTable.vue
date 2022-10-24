<template>
<div>
  <v-tabs
    v-model="tab"
    >
    <v-tab>{{ $t('GenericTemplateTable.sponsor_tab') }}</v-tab>
    <v-tab>{{ $t('GenericTemplateTable.user_tab') }}</v-tab>
  </v-tabs>
  <v-tabs-items
    v-model="tab"
    >
    <v-tab-item>
      <generic-sponsor-template-table
        ref="sponsorTable"
        :headers="headers"
        v-bind="$attrs"
        v-on="$listeners"
        has-api
        >
        <template v-for="(_, slot) of $scopedSlots" v-slot:[slot]="scope">
          <slot :name="slot" v-bind="scope" />
        </template>
      </generic-sponsor-template-table>
    </v-tab-item>
    <v-tab-item>
      <generic-user-template-table
        v-bind="$attrs"
        v-on="$listeners"
        />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import Vue from 'vue'
import GenericSponsorTemplateTable from './GenericSponsorTemplateTable'
import GenericUserTemplateTable from './GenericUserTemplateTable'

export default Vue.extend({
  name: 'studybuilder-template-table',
  props: {
    headers: {
      type: Array,
      default: function () {
        return [
          {
            text: '',
            value: 'actions',
            sortable: false,
            width: '5%'
          },
          { text: this.$t('_global.template'), value: 'name', width: '30%' },
          { text: this.$t('_global.modified'), value: 'startDate' },
          { text: this.$t('_global.status'), value: 'status' },
          { text: this.$t('_global.version'), value: 'version' }
        ]
      }
    }
  },
  components: {
    GenericSponsorTemplateTable,
    GenericUserTemplateTable
  },
  data () {
    return {
      tab: null
    }
  }
})
</script>
