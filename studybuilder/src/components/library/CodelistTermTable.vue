<template>
<div>
  <codelist-summary :codelist-names="codelistNames" :codelist-attributes="codelistAttributes" />
  <n-n-table
    :headers="headers"
    :items="terms"
    :server-items-length="total"
    :options.sync="options"
    export-object-label="Terms"
    item-key="termUid"
    height="40vh"
    class="mt-4"
    has-api
    @filter="fetchTerms"
    column-data-resource="ct/terms"
    :codelist-uid="codelistUid"
    >
    <template v-slot:actions="">
      <v-btn
        v-if="codelistAttributes.extensible"
        fab
        dark
        small
        color="primary"
        data-cy="add-term-button"
        @click.stop="showCreationForm = true"
        :title="$t('CodelistTermCreationForm.title')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.name.status="{ item }">
      <status-chip :status="item.name.status" />
    </template>
    <template v-slot:item.name.startDate="{ item }">
      {{ item.name.startDate|date }}
    </template>
    <template v-slot:item.attributes.status="{ item }">
      <status-chip :status="item.attributes.status" />
    </template>
    <template v-slot:item.attributes.startDate="{ item }">
      {{ item.attributes.startDate|date }}
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
  </n-n-table>
  <v-dialog
    v-model="showCreationForm"
    persistent
    max-width="1024px"
    content-class="top-dialog"
    >
    <codelist-term-creation-form
      :catalogueName="codelistNames.catalogueName"
      :codelistUid="codelistNames.codelistUid"
      @close="closeForm"
      @created="goToTerm"
      />
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import controlledTerminology from '@/api/controlledTerminology'
import terms from '@/api/controlledTerminology/terms'
import ActionsMenu from '@/components/tools/ActionsMenu'
import CodelistSummary from '@/components/library/CodelistSummary'
import CodelistTermCreationForm from '@/components/library/CodelistTermCreationForm'
import NNTable from '@/components/tools/NNTable'
import StatusChip from '@/components/tools/StatusChip'

export default {
  props: ['codelistUid', 'packageName', 'catalogueName'],
  components: {
    ActionsMenu,
    CodelistSummary,
    CodelistTermCreationForm,
    NNTable,
    StatusChip
  },
  computed: {
    ...mapGetters({
      currentCatalogue: 'ctCatalogues/currentCatalogue'
    })
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editTerm
        },
        {
          label: this.$t('CtCatalogueTable.remove_term'),
          icon: 'mdi-delete',
          iconColor: 'primary',
          click: this.removeTerm,
          condition: (item) => this.codelistAttributes.extensible
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history'
        }
      ],
      codelistNames: {},
      codelistAttributes: {},
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('_global.library'), value: 'libraryName' },
        { text: this.$t('CtCatalogueTable.concept_id'), value: 'termUid' },
        { text: this.$t('CodelistTermsView.sponsor_name'), value: 'name.sponsorPreferredName' },
        { text: this.$t('_global.order'), value: 'name.order' },
        { text: this.$t('CodelistTermsView.name_status'), value: 'name.status' },
        { text: this.$t('CodelistTermsView.name_date'), value: 'name.startDate' },
        { text: this.$t('CodelistTermsView.name_submission_value'), value: 'attributes.nameSubmissionValue' },
        { text: this.$t('CodelistTermsView.code_submission_value'), value: 'attributes.codeSubmissionValue' },
        { text: this.$t('CtCatalogueTable.nci_pref_name'), value: 'attributes.nciPreferredName' },
        { text: this.$t('_global.definition'), value: 'attributes.definition' },
        { text: this.$t('CodelistTermsView.attr_status'), value: 'attributes.status' },
        { text: this.$t('CodelistTermsView.attr_date'), value: 'attributes.startDate' }
      ],
      options: {},
      showCreationForm: false,
      terms: [],
      total: 0
    }
  },
  mounted () {
    controlledTerminology.getCodelistNames(this.codelistUid).then(resp => {
      this.codelistNames = resp.data
    })
    controlledTerminology.getCodelistAttributes(this.codelistUid).then(resp => {
      this.codelistAttributes = resp.data
    })
  },
  methods: {
    fetchTerms (filters, sort, filtersUpdated) {
      if (filtersUpdated) {
        this.options.page = 1
      }
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      if (this.packageName !== undefined) {
        params.package = this.packageName
      }
      if (filters !== undefined) {
        params.filters = this.filters
      }
      if (this.options.sortBy.length !== 0 && sort !== undefined) {
        params.sortBy = `{"${this.options.sortBy[0]}":${!sort}}`
      }
      params.codelist_uid = this.codelistUid
      terms.getAll(params).then(resp => {
        this.terms = resp.data.items
        this.total = resp.data.total
      })
    },
    removeTerm (term) {
      controlledTerminology.removeTermFromCodelist(this.codelistUid, term.termUid).then(resp => {
        this.fetchTerms()
        bus.$emit('notification', { msg: this.$t('CodelistTermCreationForm.remove_success') })
      })
    },
    closeForm () {
      this.showCreationForm = false
      this.fetchTerms()
    },
    goToTerm (term) {
      this.editTerm(term)
      bus.$emit('notification', { msg: this.$t('CodelistTermCreationForm.add_success') })
    },
    editTerm (term) {
      if (this.packageName) {
        this.$router.push({
          name: 'CtPackageTermDetail',
          params: {
            catalogueName: this.catalogueName,
            packageName: this.packageName,
            codelistId: term.codelistUid,
            termId: term.termUid
          }
        })
      } else {
        this.$router.push({ name: 'CodelistTermDetail', params: { codelistId: term.codelistUid, termId: term.termUid } })
      }
    }
  },
  watch: {
    options: {
      handler () {
        this.fetchTerms()
      },
      deep: true
    },
    packageName (newValue, oldValue) {
      if (newValue !== oldValue) {
        this.fetchTerms()
      }
    }
  }

}
</script>
