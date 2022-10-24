<template>
<div>
  <n-n-table
    :headers="headers"
    :items="codelists"
    :server-items-length="total"
    :options.sync="options"
    :page="currentCataloguePage"
    export-object-label="Codelists"
    :export-data-url="columnDataResource"
    item-key="codelistUid"
    @update:page="storeCurrentPage"
    dense
    has-api
    @filter="fetchCodelists"
    :column-data-resource="columnDataResource"
    :column-data-parameters="getPackageObject()"
    has-history
    :library="library"
    >
    <template v-slot:actions="">
      <slot name="extraActions"></slot>
      <v-btn
        data-cy="add-sponsor-codelist"
        v-if="!readOnly"
        fab
        dark
        small
        color="primary"
        @click.stop="showCreationForm = true"
        :title="$t('CodelistCreationForm.title')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
    <template v-slot:item.name.templateParameter="{ item }">
      {{ item.name.templateParameter|yesno }}
    </template>
    <template v-slot:item.name.status="{ item }">
      <status-chip :status="item.name.status" />
    </template>
    <template v-slot:item.name.startDate="{ item }">
      {{ item.name.startDate | date }}
    </template>
    <template v-slot:item.attributes.extensible="{ item }">
      {{ item.attributes.extensible|yesno }}
    </template>
    <template v-slot:item.attributes.status="{ item }">
      <status-chip :status="item.attributes.status" />
    </template>
    <template v-slot:item.attributes.startDate="{ item }">
      {{ item.attributes.startDate | date }}
    </template>
  </n-n-table>
  <v-dialog
    v-if="!readOnly"
    v-model="showCreationForm"
    persistent
    max-width="1200px"
    >
    <codelist-creation-form
      :catalogue="catalogue"
      @close="showCreationForm = false"
      @created="goToCodelist"
      />
  </v-dialog>
  <v-dialog v-model="showSponsorValuesHistory"
            persistent
            max-width="1200px">
    <history-table
      @close="showSponsorValuesHistory = false"
      type="codelistSponsorValues"
      url-prefix=""
      :item="selectedCodelist"
      :title-label="$t('CodelistTable.history_title')"
      :headers="historyHeaders"
      />
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import controlledTerminology from '@/api/controlledTerminology'
import ActionsMenu from '@/components/tools/ActionsMenu'
import CodelistCreationForm from '@/components/library/CodelistCreationForm'
import HistoryTable from '@/components/library/HistoryTable'
import NNTable from '@/components/tools/NNTable'
import StatusChip from '@/components/tools/StatusChip'
import filteringParameters from '@/utils/filteringParameters'

export default {
  props: {
    catalogue: {
      type: String,
      required: false
    },
    package: {
      type: String,
      required: false
    },
    readOnly: {
      type: Boolean,
      default: false
    },
    columnDataResource: String,
    library: String
  },
  components: {
    ActionsMenu,
    CodelistCreationForm,
    HistoryTable,
    NNTable,
    StatusChip
  },
  computed: {
    ...mapGetters({
      currentCataloguePage: 'ctCatalogues/currentCataloguePage'
    })
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => !this.readOnly,
          click: this.openCodelistDetail
        },
        {
          label: this.$t('CodelistTable.show_terms'),
          icon: 'mdi-dots-horizontal-circle',
          click: this.openCodelistTerms
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openCodelistHistory
        }
      ],
      codelists: [],
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('_global.library'), value: 'libraryName' },
        { text: this.$t('CtCatalogueTable.concept_id'), value: 'codelistUid' },
        { text: this.$t('CtCatalogueTable.sponsor_pref_name'), value: 'name.name', width: '15%' },
        { text: this.$t('CtCatalogueTable.template_parameter'), value: 'name.templateParameter' },
        { text: this.$t('CtCatalogueTable.cd_status'), value: 'name.status' },
        { text: this.$t('CtCatalogueTable.modified_name'), value: 'name.startDate' },
        { text: this.$t('CtCatalogueTable.cd_name'), value: 'attributes.name' },
        { text: this.$t('CtCatalogueTable.submission_value'), value: 'attributes.submissionValue' },
        { text: this.$t('CtCatalogueTable.nci_pref_name'), value: 'attributes.nciPreferredName' },
        { text: this.$t('CtCatalogueTable.extensible'), value: 'attributes.extensible' },
        { text: this.$t('CtCatalogueTable.attr_status'), value: 'attributes.status' },
        { text: this.$t('CtCatalogueTable.modified_attributes'), value: 'attributes.startDate' }
      ],
      historyHeaders: [
        { text: this.$t('_global.library'), value: 'libraryName' },
        { text: this.$t('_global.name'), value: 'name' },
        { text: this.$t('HistoryTable.change_description'), value: 'changeDescription' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.user'), value: 'userInitials' },
        { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
        { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
      ],
      options: {},
      showCreationForm: false,
      showSponsorValuesHistory: false,
      selectedCodelist: null,
      total: 0,
      filters: ''
    }
  },
  methods: {
    getPackageObject () {
      return { package: this.package }
    },
    fetchCodelists (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.library = this.library
      if (this.catalogue && this.catalogue !== 'All') {
        params.cataloguename = this.catalogue
      } else if (this.package) {
        params.package = this.package
      }
      controlledTerminology.getCodelists(params).then(resp => {
        this.codelists = resp.data.items
        this.total = resp.data.total
      })
    },
    goToCodelist (codelist) {
      this.$router.push({ name: 'CodeListDetail', params: { codelistId: codelist.codelistUid } })
      bus.$emit('notification', { msg: this.$t('CodelistCreationForm.add_success') })
    },
    openCodelistDetail (codelist) {
      this.$router.push({ name: 'CodeListDetail', params: { catalogueName: this.catalogue, codelistId: codelist.codelistUid } })
    },
    openCodelistTerms (codelist) {
      const params = { codelist }
      if (this.catalogue) {
        params.catalogueName = this.catalogue
      }
      if (this.package) {
        params.packageName = this.package
      }
      this.$emit('openCodelistTerms', params)
    },
    openCodelistHistory (codelist) {
      this.selectedCodelist = codelist
      this.showSponsorValuesHistory = true
    },
    storeCurrentPage (page) {
      this.$store.commit('ctCatalogues/SET_CURRENT_CATALOGUE_PAGE', page)
    }
  },
  watch: {
    options: {
      handler () {
        this.fetchCodelists()
      },
      deep: true
    },
    package (newValue, oldValue) {
      if (newValue !== oldValue) {
        this.codelists = []
        this.fetchCodelists()
      }
    }
  }
}
</script>
