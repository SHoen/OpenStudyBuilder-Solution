<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('DictionaryTermTable.unii_title') }}
    <help-button :help-text="$t('_help.UniiTable.general')" />
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
      dictionaryName: 'UNII',
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('DictionaryTermTable.unii_id'), value: 'dictionary_id' },
        { text: this.$t('DictionaryTermTable.substance_name'), value: 'name' },
        { text: this.$t('DictionaryTermTable.substance_name_lower_case'), value: 'name_sentence_case' },
        { text: this.$t('DictionaryTermTable.abbreviation'), value: 'abbreviation' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.modified'), value: 'start_date' }
      ]
    }
  },
  mounted () {
    dictionaries.getCodelists(this.dictionaryName).then(resp => {
      this.codelistUid = resp.data.items[0].codelist_uid
    })
  }
}
</script>
