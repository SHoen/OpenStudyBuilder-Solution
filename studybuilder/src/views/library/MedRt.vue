<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('DictionaryTermTable.medrt_title') }}
    <help-button :help-text="$t('_help.MedRtTable.general')" />
  </div>
  <dictionary-term-table
    :codelist-uid="codelistUid"
    :dictionary-name="dictionaryName"
    :headers="headers"
    column-data-resource="dictionaries/terms"
    />
</div>
</template>

<script>
import dictionaries from '@/api/dictionaries'
import DictionaryTermTable from '@/components/library/DictionaryTermTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    DictionaryTermTable,
    HelpButton
  },
  data () {
    return {
      codelistUid: null,
      dictionaryName: 'MED-RT',
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('DictionaryTermTable.medrt_id'), value: 'dictionaryId' },
        { text: this.$t('DictionaryTermTable.class_name'), value: 'name' },
        { text: this.$t('DictionaryTermTable.class_name_lower_case'), value: 'nameSentenceCase' },
        { text: this.$t('DictionaryTermTable.abbreviation'), value: 'abbreviation' },
        { text: this.$t('_global.definition'), value: 'definition' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.modified'), value: 'startDate' }
      ]
    }
  },
  mounted () {
    dictionaries.getCodelists(this.dictionaryName).then(resp => {
      this.codelistUid = resp.data.items[0].codelistUid
    })
  }
}
</script>
