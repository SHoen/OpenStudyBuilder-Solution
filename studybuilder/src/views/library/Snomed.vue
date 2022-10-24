<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('DictionaryTermTable.snomed_title') }}
    <help-button :help-text="$t('_help.SnomedTable.general')" />
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
      dictionaryName: 'SNOMED',
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('DictionaryTermTable.snomed_id'), value: 'dictionaryId' },
        { text: this.$t('DictionaryTermTable.preferred_synonym'), value: 'name' },
        { text: this.$t('DictionaryTermTable.preferred_synonym_lower_case'), value: 'nameSentenceCase' },
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
