<template>
<div>
  <n-n-table
    :headers="actualHeaders"
    export-object-label="Snomed"
    :export-data-url="columnDataResource"
    item-key="uid"
    :server-items-length="total"
    :options.sync="options"
    has-api
    :items="items"
    @filter="fetchTerms"
    :column-data-resource="columnDataResource"
    :codelistUid="codelistUid"
    >
    <template v-slot:actions="">
      <v-btn
        fab
        dark
        small
        color="primary"
        @click="createTerm()"
        :title="$t('DictionaryTermTable.add_title')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.status="{ item }">
      <status-chip :status="item.status" />
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate | date }}
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
  </n-n-table>
  <slot name="termForm" :closeForm="closeForm" :open="showTermForm">
    <dictionary-term-form
      :open="showTermForm"
      @close="closeForm"
      :dictionaryName="dictionaryName"
      :editedTerm="formToEdit"
      :editedTermCategory="codelistUid"
      @save="fetchTerms"
      />
  </slot>
</div>
</template>

<script>
import dictionaries from '@/api/dictionaries'
import ActionsMenu from '@/components/tools/ActionsMenu'
import DictionaryTermForm from '@/components/library/DictionaryTermForm'
import NNTable from '@/components/tools/NNTable'
import StatusChip from '@/components/tools/StatusChip'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    DictionaryTermForm,
    NNTable,
    StatusChip
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) => item.possibleActions.find(action => action === 'approve'),
          click: this.approveTerm
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'edit'),
          click: this.editTerm
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'newVersion'),
          click: this.newTermVersion
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'inactivate'),
          click: this.inactivateTerm
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'reactivate'),
          click: this.reactivateTerm
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => item.possibleActions.find(action => action === 'delete'),
          click: this.deleteTerm
        }
      ],
      defaultHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.dictionaryName, value: 'dictionaryId' },
        { text: this.$t('_global.name'), value: 'name' },
        { text: this.$t('DictionaryTermTable.lower_case_name'), value: 'nameSentenceCase' },
        { text: this.$t('DictionaryTermTable.abbreviation'), value: 'abbreviation' },
        { text: this.$t('_global.definition'), value: 'definition' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.modified'), value: 'startDate' }
      ],
      total: 0,
      options: {},
      items: [],
      showTermForm: false,
      formToEdit: {}
    }
  },
  props: {
    codelistUid: String,
    columnDataResource: String,
    dictionaryName: String,
    headers: {
      type: Array,
      required: false
    }
  },
  computed: {
    actualHeaders () {
      return (this.headers) ? this.headers : this.defaultHeaders
    }
  },
  methods: {
    fetchTerms (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.codelist_uid = this.codelistUid
      if (params.codelist_uid !== null) {
        dictionaries.getTerms(params).then(resp => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
      }
    },
    inactivateTerm (item) {
      dictionaries.inactivate(item.termUid).then(resp => {
        this.fetchTerms()
      })
    },
    reactivateTerm (item) {
      dictionaries.reactivate(item.termUid).then(resp => {
        this.fetchTerms()
      })
    },
    deleteTerm (item) {
      dictionaries.delete(item.termUid).then(resp => {
        this.fetchTerms()
      })
    },
    approveTerm (item) {
      dictionaries.approve(item.termUid).then(resp => {
        this.fetchTerms()
      })
    },
    newTermVersion (item) {
      dictionaries.newVersion(item.termUid).then(resp => {
        this.fetchTerms()
      })
    },
    editTerm (item) {
      this.formToEdit = item
      this.showTermForm = true
    },
    createTerm () {
      this.formToEdit = null
      this.showTermForm = true
    },
    closeForm () {
      this.formToEdit = null
      this.showTermForm = false
    }
  },
  watch: {
    options: {
      handler () {
        this.fetchTerms()
      },
      deep: true
    },
    codelistUid () {
      this.fetchTerms()
    }
  }
}
</script>
