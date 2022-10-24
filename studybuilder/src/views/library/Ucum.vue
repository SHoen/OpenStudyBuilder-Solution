<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('DictionaryTermTable.ucum_title') }}
    <help-button :help-text="$t('_help.UcumTable.general')" />
  </div>
  <dictionary-term-table
    :codelist-uid="codelistUid"
    :dictionary-name="dictionaryName"
    :headers="headers"
    column-data-resource="dictionaries/terms"
    >
    <template v-slot:termForm="{ closeForm, open }">
      <ucum-code-form
        :open="open"
        :codelist-uid="codelistUid"
        @close="closeForm"
        />
    </template>
  </dictionary-term-table>
</div>
</template>

<script>
import dictionaries from '@/api/dictionaries'
import DictionaryTermTable from '@/components/library/DictionaryTermTable'
import UcumCodeForm from '@/components/library/UCUMCodeForm'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    DictionaryTermTable,
    UcumCodeForm,
    HelpButton
  },
  data () {
    return {
      codelistUid: null,
      dictionaryName: 'UCUM',
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('UCUM.code'), value: 'name' },
        { text: this.$t('UCUM.description'), value: 'definition' },
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
