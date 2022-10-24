<template>
<div>
  <n-n-table
    key="endpointTable1"
    :headers="headers"
    :items="studyEndpoints"
    item-key="order"
    has-api
    :column-data-resource="`study/${selectedStudy.uid}/study-endpoints`"
    :export-data-url="exportDataUrl"
    :options.sync="options"
    :server-items-length="total"
    @filter="fetchEndpoints"
    >
    <template v-slot:afterSwitches>
      <div :title="$t('NNTableTooltips.reorder_content')">
        <v-switch
          v-model="sortMode"
          :label="$t('NNTable.reorder_content')"
          hide-details
          class="mr-6"
          />
      </div>
    </template>
    <template v-slot:actions="">
      <slot name="extraActions"></slot>
      <v-btn
        fab
        dark
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('StudyEndpointsTable.add_endpoint')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:body="props" v-if="sortMode">
      <draggable
        :list="props.items"
        tag="tbody"
        :move="checkEndpointLevel"
        @change="onChange($event)"
        >
        <tr
          v-for="(item, index) in props.items"
          :key="index"
          >
          <td width="3%">
            <actions-menu :actions="actions" :item="item"/>
          </td>
          <td width="5%">
            <v-icon
              small
              class="page__grab-icon">
              mdi-sort
            </v-icon>
            {{ item.order }}
          </td>
          <td width="25%">
            <n-n-parameter-highlighter
              v-if="item.endpoint"
              :name="item.endpoint.name"
              :show-prefix-and-postfix="false"
              />
          </td>
          <td>
            <template v-if="item.endpointLevel">{{ item.endpointLevel.sponsorPreferredName }}</template>
          </td>
          <td width="10%">{{ displayUnits(item.endpointUnits) }}</td>
          <td width="25%">
            <n-n-parameter-highlighter
              v-if="item.timeframe"
              :name="item.timeframe.name"
              :show-prefix-and-postfix="false"
              />
          </td>
          <td width="25%">
            <n-n-parameter-highlighter
              v-if="item.studyObjective"
              :name="item.studyObjective.objective.name"
              :show-prefix-and-postfix="false"
              />
            <span v-else>{{ $t('StudyEndpointForm.select_later') }}</span>
          </td>
          <td width="10%">{{ item.startDate | date }}</td>
          <td width="10%">{{ item.userInitials }}</td>
        </tr>
      </draggable>
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item"/>
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate | date }}
    </template>
    <template v-slot:item.endpoint.name="{ item }">
    <v-row>
      <n-n-parameter-highlighter
        v-if="item.endpoint"
        :name="item.endpoint.name"
        :show-prefix-and-postfix="false"
        />
      <v-tooltip bottom>
        <template v-slot:activator="{ on, attrs }">
          <v-icon
            v-if="item.endpoint && item.endpoint.name.length > 254"
            class="mb-2 ml-1"
            v-bind="attrs"
            v-on="on"
            color="red">
              mdi-alert-circle
            </v-icon>
        </template>
        <span>{{ $t('StudyEndpointForm.endpoint_title_warning') }}</span>
      </v-tooltip>
    </v-row>
    </template>
    <template v-slot:item.studyObjective="{ item }">
      <n-n-parameter-highlighter
        v-if="item.studyObjective"
        :name="item.studyObjective.objective.name"
        :show-prefix-and-postfix="false"
        />
      <span v-else>{{ $t('StudyEndpointForm.select_later') }}</span>
    </template>
    <template v-slot:item.endpointUnits.units="{ item }">
      {{ displayUnits(item.endpointUnits) }}
    </template>
    <template v-slot:item.timeframe.name="{ item }">
      <n-n-parameter-highlighter
        v-if="item.timeframe"
        :name="item.timeframe.name"
        :show-prefix-and-postfix="false"
        />
      <span v-else>{{ $t('StudyEndpointForm.select_later') }}</span>
    </template>
  </n-n-table>
  <v-dialog v-model="showForm"
            persistent
            fullscreen
            hide-overlay
            content-class="fullscreen-dialog"
            >
    <endpoint-form
      :study-endpoint="selectedStudyEndpoint"
      @close="closeForm"
      class="fullscreen-dialog"
      />
  </v-dialog>
  <v-dialog v-model="showHistory"
            persistent
            max-width="1200px">
    <history-table
      @close="closeHistory"
      type="studyEndpoint"
      :item="selectedStudyEndpoint"
      :title-label="$t('StudyEndpointsTable.history_title')"
      />
  </v-dialog>
  <confirm-dialog ref="confirm" width="600"/>
  <v-snackbar
    v-model="snackbar"
    color="error"
    top
    >
    <v-icon class="mr-2">mdi-alert</v-icon>
    {{ $t('StudyEndpointsTable.sort_help_msg') }}
  </v-snackbar>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import study from '@/api/study'
import ActionsMenu from '@/components/tools/ActionsMenu'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import EndpointForm from '@/components/studies/EndpointForm'
import HistoryTable from '@/components/library/HistoryTable'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import statuses from '@/constants/statuses'
import NNTable from '@/components/tools/NNTable'
import draggable from 'vuedraggable'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    NNParameterHighlighter,
    EndpointForm,
    HistoryTable,
    ConfirmDialog,
    NNTable,
    draggable
  },
  computed: {
    ...mapGetters({
      units: 'studiesGeneral/allUnits',
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyEndpoints: 'studyEndpoints/studyEndpoints'
    }),
    filteredHeaders () {
      return this.headers.filter(header => header.show === true || header.show === undefined)
    },
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-endpoints`
    }
  },
  data () {
    return {
      abortConfirm: false,
      actions: [
        {
          label: this.$t('StudyEndpointsTable.update_timeframe_version_retired'),
          icon: 'mdi-alert',
          iconColor: 'orange',
          condition: this.isTimeframeRetired
        },
        {
          label: this.$t('StudyEndpointsTable.update_timeframe_version'),
          icon: 'mdi-bell-ring',
          iconColorFunc: this.itemUpdateAborted,
          condition: this.timeframeNeedsUpdate,
          click: this.updateTimeframeVersion
        },
        {
          label: this.$t('StudyEndpointsTable.update_endpoint_version_retired'),
          icon: 'mdi-alert',
          iconColor: 'orange',
          condition: this.isEndpointRetired
        },
        {
          label: this.$t('StudyEndpointsTable.update_endpoint_version'),
          icon: 'mdi-bell-ring',
          iconColorFunc: this.itemUpdateAborted,
          condition: this.endpointNeedsUpdate,
          click: this.updateEndpointVersion
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editStudyEndpoint
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteStudyEndpoint
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openObjectiveHistory
        }
      ],
      actionsMenu: false,
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyEndpointsTable.order'), value: 'order', width: '5%' },
        { text: this.$t('StudyEndpointsTable.endpoint_title'), value: 'endpoint.name', width: '25%' },
        { text: this.$t('StudyEndpointsTable.endpoint_level'), value: 'endpointLevel.sponsorPreferredName' },
        { text: this.$t('StudyEndpointsTable.endpoint_sub_level'), value: 'endpointSubLevel.sponsorPreferredName' },
        { text: this.$t('StudyEndpointsTable.units'), value: 'endpointUnits.units', width: '10%' },
        { text: this.$t('StudyEndpointsTable.time_frame'), value: 'timeframe.name', width: '25%' },
        { text: this.$t('StudyEndpointsTable.objective'), value: 'studyObjective', filteringName: 'studyObjective.objective.name', width: '25%' },
        { text: this.$t('_global.modified'), value: 'startDate', width: '10%' },
        { text: this.$t('_global.modified_by'), value: 'userInitials', width: '10%' }
      ],
      selectedStudyEndpoint: null,
      showForm: false,
      showHistory: false,
      snackbar: false,
      sortBy: 'startDate',
      sortMode: false,
      endpoints: [],
      total: 0,
      options: {}
    }
  },
  methods: {
    fetchEndpoints (filters, sort, filtersUpdated) {
      if (this.options.sortBy.length > 0) {
        const filterName = this.headers.find(header => header.value === this.options.sortBy[0]).filteringName
        if (filterName) {
          this.options.sortBy[0] = filterName
        }
      }
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.studyUid = this.selectedStudy.uid
      this.$store.dispatch('studyEndpoints/fetchStudyEndpoints', params).then(resp => {
        this.total = resp.data.total
      })
    },
    actionsMenuBadge (item) {
      if (this.endpointNeedsUpdate(item) || this.timeframeNeedsUpdate(item)) {
        return {
          color: 'error',
          icon: 'mdi-bell'
        }
      }
      return null
    },
    timeframeNeedsUpdate (item) {
      if (item.latestTimeframe) {
        if (!this.isTimeframeRetired(item)) {
          return item.timeframe.version !== item.latestTimeframe.version
        }
      }
      return false
    },
    isTimeframeRetired (item) {
      if (item.latestTimeframe) {
        return item.latestTimeframe.status === statuses.RETIRED
      }
      return false
    },
    async updateTimeframeVersion (item) {
      const options = {
        type: 'warning',
        width: 1000,
        cancelLabel: this.$t('StudyObjectivesTable.keep_old_version'),
        agreeLabel: this.$t('StudyObjectivesTable.use_new_version')
      }
      const message = this.$t('StudyEndpointsTable.update_timeframe_version_alert') + '<br><br>' +
      '<h4 class="confirmation-text-header">' + this.$t('StudyEndpointsTable.previous_version') + '</h4>' +
      '<p class="confirmation-text-field">' + item.timeframe.name + '</p>' +
      '<h4 class="confirmation-text-header">' + this.$t('StudyEndpointsTable.new_version') + '</h4>' +
      '<p class="confirmation-text-field">' + item.latestTimeframe.name + '</p>'

      if (await this.$refs.confirm.open(message, options)) {
        const args = {
          studyUid: item.studyUid,
          studyEndpointUid: item.studyEndpointUid
        }
        this.$store.dispatch('studyEndpoints/updateStudyEndpointTimeframeLatestVersion', args).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyObjectivesTable.update_version_successful') })
        })
      } else {
        this.abortConfirm = true
        const args = {
          studyUid: item.studyUid,
          studyObjectiveUid: item.studyEndpointUid
        }
        this.$store.dispatch('studyEndpoints/updateStudyEndpointAcceptVersion', args).then(resp => {
        })
      }
    },
    endpointNeedsUpdate (item) {
      if (item.latestEndpoint) {
        if (!this.isEndpointRetired(item)) {
          return item.endpoint.version !== item.latestEndpoint.version
        }
      }
      return false
    },
    isEndpointRetired (item) {
      if (item.latestEndpoint) {
        return item.latestEndpoint.status === statuses.RETIRED
      }
      return false
    },
    itemUpdateAborted (item) {
      return item.acceptedVersion ? '' : 'error'
    },
    async updateEndpointVersion (item) {
      const options = {
        type: 'warning',
        width: 1200,
        cancelLabel: this.$t('StudyObjectivesTable.keep_old_version'),
        agreeLabel: this.$t('StudyObjectivesTable.use_new_version')
      }
      const message = this.$t('StudyEndpointsTable.update_endpoint_version_alert') + ' ' + this.$t('StudyEndpointsTable.previous_version') +
      ' ' + item.endpoint.name + ' ' + this.$t('StudyEndpointsTable.new_version') + ' ' + item.latestEndpoint.name

      if (await this.$refs.confirm.open(message, options)) {
        const args = {
          studyUid: item.studyUid,
          studyObjectiveUid: item.studyEndpointUid
        }
        this.$store.dispatch('studyEndpoints/updateStudyEndpointEndpointLatestVersion', args).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyEndpointsTable.update_version_successful') })
        })
      } else {
        this.abortConfirm = true
        const args = {
          studyUid: item.studyUid,
          studyEndpointUid: item.studyEndpointUid
        }
        this.$store.dispatch('studyEndpoints/updateStudyEndpointAcceptVersion', args).then(resp => {
        })
      }
    },
    closeForm () {
      this.showForm = false
      this.selectedStudyEndpoint = null
      this.fetchEndpoints()
    },
    getHeaderLabel (value) {
      return this.headers.filter(item => item.value === value)[0].text
    },
    editStudyEndpoint (studyEndpoint) {
      this.selectedStudyEndpoint = studyEndpoint
      this.showForm = true
    },
    getUnitName (unitUid) {
      for (let cpt = 0; cpt < this.units.length; cpt++) {
        const unit = this.units[cpt]
        if (unit.uid === unitUid) {
          return unit.name
        }
      }
      return ''
    },
    displayUnits (units) {
      const unitNames = units.units.map(unit => this.getUnitName(unit))
      if (unitNames.length > 1) {
        return unitNames.join(` ${units.separator} `)
      }
      return unitNames[0]
    },
    async deleteStudyEndpoint (studyEndpoint) {
      const options = { type: 'warning' }
      let endpoint = studyEndpoint.endpoint.name

      endpoint = endpoint.replaceAll(/\[|\]/g, '')
      if (await this.$refs.confirm.open(this.$t('StudyEndpointsTable.confirm_delete', { endpoint }), options)) {
        // Make sure to set current studyObjective so the list of
        // endpoints is updated after deletion
        this.$store.dispatch('studyEndpoints/deleteStudyEndpoint', {
          studyUid: this.selectedStudy.uid,
          studyEndpointUid: studyEndpoint.studyEndpointUid
        }).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyEndpointsTable.delete_success') })
          this.fetchEndpoints()
        })
      }
    },
    closeHistory () {
      this.selectedStudyEndpoint = null
      this.showHistory = false
    },
    openObjectiveHistory (studyEndpoint) {
      this.selectedStudyEndpoint = studyEndpoint
      this.showHistory = true
    },
    /*
    ** Prevent dragging between different endpoint levels
    */
    checkEndpointLevel (event) {
      const leftOrder = event.draggedContext.element.endpointLevel ? event.draggedContext.element.endpointLevel.order : null
      const rightOrder = event.relatedContext.element.endpointLevel ? event.relatedContext.element.endpointLevel.order : null
      const result = leftOrder === rightOrder
      this.snackbar = !result
      return result
    },
    onChange (event) {
      const studyEndpoint = event.moved.element
      const newOrder = this.studyEndpoints[event.moved.newIndex].order
      study.updateStudyEndpointOrder(studyEndpoint.studyUid, studyEndpoint.studyEndpointUid, newOrder).then(resp => {
      })
    }
  },
  mounted () {
    this.$store.dispatch('studiesGeneral/fetchAllUnits')
    this.$store.dispatch('studiesGeneral/fetchEndpointLevels')
    this.$store.dispatch('studiesGeneral/fetchEndpointSubLevels')
    this.fetchEndpoints()
  },
  watch: {
    sortMode (value) {
      this.$set(this.headers[0], 'show', value)
      this.headers.forEach(header => {
        this.$set(header, 'sortable', !value)
      })
      this.sortBy = (value) ? 'order' : 'startDate'
    },
    options () {
      this.fetchEndpoints()
    }
  }
}
</script>
<style scoped>
.roundChip {
  width: 25px;
  justify-content: space-evenly;
}
</style>
