<template>
<div>
  <n-n-table
    :headers="headers"
    :items="timeframes"
    export-object-label="Timeframes"
    export-data-url="/timeframes"
    item-key="uid"
    sort-by="startDate"
    sort-desc
    has-api
    @filter="fetchTimeframes"
    column-data-resource="timeframes"
    :options.sync="options"
    >
    <template v-slot:actions="">
      <v-btn
        fab
        dark
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('TimeframeForm.add_title')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.name="{ item }">
      <n-n-parameter-highlighter :name="item.name" :show-prefix-and-postfix="false" />
    </template>
    <template v-slot:item.timeframeTemplate.name="{ item }">
      <n-n-parameter-highlighter :name="item.timeframeTemplate.name" default-color="orange" />
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
  <timeframe-form
    :open="showForm"
    @close="closeForm"
    :timeframe="selectedObject" />
  <v-dialog v-model="showHistory"
            persistent
            max-width="1200px">
    <history-table @close="closeHistory" type="timeframe" url-prefix="/timeframes/" :item="selectedObject"
                   :title-label="$t('TimeframeTable.singular_title')" />
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import ActionsMenu from '@/components/tools/ActionsMenu'
import HistoryTable from '@/components/library/HistoryTable'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import StatusChip from '@/components/tools/StatusChip'
import TimeframeForm from '@/components/library/TimeframeForm'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    HistoryTable,
    NNParameterHighlighter,
    NNTable,
    StatusChip,
    TimeframeForm
  },
  computed: {
    ...mapGetters({
      timeframes: 'timeframes/timeframes'
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
          click: this.approveObject
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'edit'),
          click: this.editObject
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'inactivate'),
          click: this.inactivateObject
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'reactivate'),
          click: this.reactivateObject
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => item.possibleActions.find(action => action === 'delete'),
          click: this.deleteObject
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
        { text: this.$t('_global.template'), value: 'timeframeTemplate.name', width: '30%' },
        { text: this.$t('_global.timeframe'), value: 'name' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: '' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' }
      ],
      showForm: false,
      showHistory: false,
      selectedObject: null,
      options: {}
    }
  },
  methods: {
    fetchTimeframes (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      this.$store.dispatch('timeframes/fetchFilteredTimeframes', params)
    },
    closeForm () {
      this.showForm = false
      this.selectedObject = null
    },
    approveObject (endpoint) {
      this.$store.dispatch('timeframes/approveObject', endpoint).then(() => {
        bus.$emit('notification', { msg: this.$t('TimeframeTable.approve_success') })
      })
    },
    closeHistory () {
      this.selectedObject = null
      this.showHistory = false
    },
    editObject (endpoint) {
      this.selectedObject = endpoint
      this.showForm = true
    },
    inactivateObject (endpoint) {
      this.$store.dispatch('timeframes/inactivateObject', endpoint).then(() => {
        bus.$emit('notification', { msg: this.$t('TimeframeTable.inactivate_success') })
      })
    },
    reactivateObject (endpoint) {
      this.$store.dispatch('timeframes/reactivateObject', endpoint).then(() => {
        bus.$emit('notification', { msg: this.$t('TimeframeTable.reactivate_success') })
      })
    },
    deleteObject (endpoint) {
      this.$store.dispatch('timeframes/deleteTimeframe', endpoint).then(() => {
        bus.$emit('notification', { msg: this.$t('TimeframeTable.delete_success') })
      })
    },
    openHistory (endpoint) {
      this.selectedObject = endpoint
      this.showHistory = true
    }
  },
  mounted () {
    this.fetchTimeframes()
  }
}
</script>
