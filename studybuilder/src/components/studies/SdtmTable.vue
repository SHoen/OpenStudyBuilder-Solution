<template>
<n-n-table
  :headers="headers"
  :items="items"
  >
</n-n-table>
</template>

<script>
import NNTable from '@/components/tools/NNTable'

export default {
  components: {
    NNTable
  },
  data () {
    return {
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('SdtmTable.studyid'), value: 'studyId' },
        { text: this.$t('SdtmTable.tsparm'), value: 'tsparm' },
        { text: this.$t('SdtmTable.tsparmcd'), value: 'tsparmcd' },
        { text: this.$t('SdtmTable.tsval'), value: 'tsval' },
        { text: this.$t('SdtmTable.tsvalnf'), value: 'tsvalcd' },
        { text: this.$t('SdtmTable.tsvalcd'), value: 'tsvalcd' },
        { text: this.$t('SdtmTable.tsvcdref'), value: 'tsvcdref' },
        { text: this.$t('SdtmTable.tsvcdver'), value: 'tsvcdver' },
        { text: this.$t('_global.modified'), value: 'modified' }
      ],
      items: []
    }
  }
}
</script>
