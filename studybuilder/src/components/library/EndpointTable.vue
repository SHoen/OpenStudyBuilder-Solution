<template>
<div>
  <n-n-table
    :headers="headers"
    :items="endpoints"
    export-object-label="Endpoints"
    export-data-url="/endpoints"
    item-key="uid"
    sort-by="startDate"
    sort-desc
    has-history
    has-api
    @filter="fetchEndpoints"
    column-data-resource="endpoints"
    :options.sync="options"
    >
    <template v-slot:actions="">
      <v-btn
        fab
        dark
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('EndpointForm.add_title')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.name="{ item }">
      <n-n-parameter-highlighter :name="item.name" :show-prefix-and-postfix="false" />
    </template>
    <template v-slot:item.endpointTemplate.name="{ item }">
      <n-n-parameter-highlighter :name="item.endpointTemplate.name" default-color="orange" />
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate | date }}
    </template>
    <template v-slot:item.status="{ item }">
      <status-chip :status="item.status" />
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
  </n-n-table>
  <endpoint-form
    :open="showForm"
    @close="closeForm"
    :endpoint="selectedEndpoint" />
  <v-dialog v-model="showHistory"
            persistent
            max-width="1200px">
    <history-table @close="closeHistory" type="endpoint" url-prefix="/endpoints/" :item="selectedEndpoint"
                   :title-label="$t('EndpointTable.singular_title')" />
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import ActionsMenu from '@/components/tools/ActionsMenu'
import EndpointForm from '@/components/library/EndpointForm'
import HistoryTable from '@/components/library/HistoryTable'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import StatusChip from '@/components/tools/StatusChip'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    EndpointForm,
    HistoryTable,
    NNParameterHighlighter,
    NNTable,
    StatusChip
  },
  computed: {
    ...mapGetters({
      endpoints: 'endpoints/endpoints'
    })
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) => item.possibleActions.find(action => action === 'approve'),
          click: this.approveEndpoint
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'edit'),
          click: this.editEndpoint
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'inactivate'),
          click: this.inactivateEndpoint
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'reactivate'),
          click: this.reactivateEndpoint
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => item.possibleActions.find(action => action === 'delete'),
          click: this.deleteEndpoint
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory
        }
      ],
      headers: [
        {
          text: '',
          value: 'actions',
          sortable: false,
          width: '5%'
        },
        { text: this.$t('_global.library'), value: 'library.name' },
        { text: this.$t('_global.template'), value: 'endpointTemplate.name', width: '30%' },
        { text: this.$t('_global.endpoint'), value: 'name' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: 'fixme' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('EndpointTable.studies_count'), value: 'studyCount' }
      ],
      showForm: false,
      showHistory: false,
      selectedEndpoint: null,
      options: {}
    }
  },
  methods: {
    fetchEndpoints (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      this.$store.dispatch('endpoints/fetchFilteredEndpoints', params)
    },
    closeForm () {
      this.showForm = false
      this.selectedEndpoint = null
    },
    approveEndpoint (endpoint) {
      this.$store.dispatch('endpoints/approveEndpoint', endpoint).then(() => {
        bus.$emit('notification', { msg: this.$t('EndpointTable.approve_success') })
      })
    },
    closeHistory () {
      this.selectedEndpoint = null
      this.showHistory = false
    },
    editEndpoint (endpoint) {
      this.selectedEndpoint = endpoint
      this.showForm = true
    },
    inactivateEndpoint (endpoint) {
      this.$store.dispatch('endpoints/inactivateEndpoint', endpoint).then(() => {
        bus.$emit('notification', { msg: this.$t('EndpointTable.inactivate_success') })
      })
    },
    reactivateEndpoint (endpoint) {
      this.$store.dispatch('endpoints/reactivateEndpoint', endpoint).then(() => {
        bus.$emit('notification', { msg: this.$t('EndpointTable.reactivate_success') })
      })
    },
    deleteEndpoint (endpoint) {
      this.$store.dispatch('endpoints/deleteEndpoint', endpoint).then(() => {
        bus.$emit('notification', { msg: this.$t('EndpointTable.delete_success') })
      })
    },
    openHistory (endpoint) {
      this.selectedEndpoint = endpoint
      this.showHistory = true
    }
  },
  mounted () {
    this.fetchEndpoints()
  }
}
</script>
