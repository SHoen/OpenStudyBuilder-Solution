<template>
<div>
  <div id="visjs" class="pa-6">
    <span class="text-h6 ml-2">{{ $t('StudyVisitTable.title') }}</span>
    <div v-if="!loading && studyVisits.length > 0" :key="chartsKey">
      <horizontal-bar-chart
        :chart-data="barChartDatasets"
        :options="barChartOptions"
        :styles="barChartStyles"
        class="pr-3"
        :key="barChartKey"
        />
      <bubble-chart
        :chart-data="lineChartDatasets"
        :options="lineChartOptions"
        :styles="lineChartStyles"
        class="ml-1"
        />
    </div>
    <div v-else-if="loading">
      <v-progress-linear
        class="mt-5"
        indeterminate
      ></v-progress-linear>
    </div>
    <div v-else class="mt-3">
      {{ $t('StudyVisitForm.no_data') }}
    </div>
  </div>
  <n-n-table
    :headers="headers"
    :default-headers="defaultColumns"
    :items="studyVisits"
    item-key="uid"
    class="mt-6"
    :export-data-url="exportDataUrl"
    has-api
    @filter="fetchStudyVisits"
    :column-data-resource="`study/${selectedStudy.uid}/study-visits`"
    :options.sync="options"
    fixed-header
    >
    <template v-slot:actions>
      <v-progress-circular
        indeterminate
        color="primary"
        v-show="loading"
        >
      </v-progress-circular>
      <v-btn
        fab
        dark
        small
        color="primary"
        @click.stop="openForm"
        v-bind="attrs"
        v-on="on"
        v-show="!loading"
        :title="$t('NNTableTooltips.add_content')"
        data-cy="add-visit"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
      <v-btn
        fab
        small
        color="primary"
        @click.stop="openEditMode"
        :title="$t('_global.edit')"
        data-cy="edit-study-visits"
        class="ml-2"
        v-if="!editMode && !loading"
        >
        <v-icon dark>
          mdi-pencil
        </v-icon>
      </v-btn>
      <v-progress-circular
        indeterminate
        color="primary"
        v-show="loading"
        class="ml-2"
        >
      </v-progress-circular>
      <v-btn
        fab
        small
        color="primary"
        @click.stop="closeEditMode"
        title="Cancel"
        class="ml-2"
        data-cy="close-edit-mode"
        v-if="editMode"
        >
        <v-icon dark>
          mdi-close-thick
        </v-icon>
      </v-btn>
      <v-btn
        fab
        dark
        class="ml-2"
        small
        color="secondary"
        :title="$t('NNTableTooltips.history')"
        data-cy="visits-version-history"
        @click="openStudyVisitsHistory()"
        >
        <v-icon dark>
          mdi-history
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.visitWindow="{ item }">
      <div v-if="editMode && item.visitClass === 'SINGLE_VISIT'">
        <v-row class="cellWidth">
          <v-col cols="3">
            <v-text-field
              dense
              v-model="item.minVisitWindowValue"
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"/>
          </v-col>
          <v-col cols="3">
            <v-text-field
              dense
              v-model="item.maxVisitWindowValue"
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"/>
          </v-col>
          <v-col cols="6">
            <v-select
              :items="timeUnits"
              item-text="name"
              item-value="uid"
              dense
              v-model="item.visitWindowUnitUid"
              :disabled="item.disabled && itemsDisabled"
              @change="disableOthers(item)"/>
          </v-col>
        </v-row>
      </div>
      <template v-else-if="item.minVisitWindowValue !== null && item.maxVisitWindowValue !== null">
        {{ item.minVisitWindowValue }} / {{ item.maxVisitWindowValue }} {{ getUnitName(item.visitWindowUnitUid) }}
      </template>
    </template>
    <template v-slot:item.studyEpochUid="{ item }">
      {{ getStudyEpochName(item.studyEpochUid) }}
    </template>
    <template v-slot:item.showVisit="{ item }">
      <div v-if="editMode && item.visitClass === 'SINGLE_VISIT'">
        <v-checkbox
          v-model="item.showVisit"
          @change="disableOthers(item)"/>
      </div>
      <div v-else>
        {{ item.showVisit|yesno}}
      </div>
    </template>
    <template v-slot:item.isGlobalAnchorVisit="{ item }">
      {{ item.isGlobalAnchorVisit|yesno}}
    </template>
    <template v-slot:item.visitSubclass="{ item }">
      {{ item.visitSubclass === 'ANCHOR_VISIT_IN_GROUP_OF_SUBV' ? 'Yes' : 'No'}}
    </template>
    <template v-slot:item.visitSubName="{ item }">
      {{ item.visitSubclass === 'ANCHOR_VISIT_IN_GROUP_OF_SUBV' ? item.visitSubName : ''}}
    </template>
    <template v-slot:item.timeValue="{ item }">
      <div v-if="editMode && item.visitClass === 'SINGLE_VISIT'">
        <v-row class="cellWidth">
          <v-col cols="4">
            <v-text-field
              dense
              v-model="item.timeValue"
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"/>
          </v-col>
          <v-col cols="6">
            <v-select
              :items="timeUnits"
              item-text="name"
              item-value="uid"
              dense
              v-model="item.timeUnitUid"
              :disabled="item.disabled && itemsDisabled"
              @change="disableOthers(item)"/>
          </v-col>
        </v-row>
      </div>
      <div v-else>
        {{ item.timeValue }} {{ getUnitName(item.timeUnitUid) }}
      </div>
    </template>
    <template v-slot:item.visitContactModeName="{ item }">
      <div v-if="editMode && item.visitClass === 'SINGLE_VISIT'">
        <v-select
        class="cellWidth"
        :items="contactModes"
        item-text="sponsorPreferredName"
        item-value="termUid"
        dense
        v-model="item.visitContactModeUid"
        :disabled="item.disabled && itemsDisabled"
        @change="disableOthers(item)"/>
      </div>
      <div v-else>
        {{ item.visitContactModeName }}
      </div>
    </template>
    <template v-slot:item.timeReferenceName="{ item }">
      <div v-if="editMode && item.visitClass === 'SINGLE_VISIT'">
        <v-select
        class="cellWidth"
        :items="timeReferences"
        item-text="sponsorPreferredName"
        item-value="termUid"
        dense
        v-model="item.timeReferenceUid"
        :disabled="item.disabled && itemsDisabled"
        @change="disableOthers(item)"/>
      </div>
      <div v-else>
        {{ item.timeReferenceName }}
      </div>
    </template>
    <template v-slot:item.description="{ item }">
      <div v-if="editMode && item.visitClass === 'SINGLE_VISIT'">
        <v-row class="cellWidth">
          <v-col>
            <v-text-field
              dense
              v-model="item.description"
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"/>
          </v-col>
        </v-row>
      </div>
      <div v-else>
        {{ item.description }}
      </div>
    </template>
    <template v-slot:item.startRule="{ item }">
      <div v-if="editMode && item.visitClass === 'SINGLE_VISIT'">
        <v-row class="cellWidth">
          <v-col>
            <v-text-field
              dense
              v-model="item.startRule"
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"/>
          </v-col>
        </v-row>
      </div>
      <div v-else>
        {{ item.startRule }}
      </div>
    </template>
    <template v-slot:item.endRule="{ item }">
      <div v-if="editMode && item.visitClass === 'SINGLE_VISIT'">
        <v-row class="cellWidth">
          <v-col>
            <v-text-field
              dense
              v-model="item.endRule"
              :disabled="item.disabled && itemsDisabled"
              @input="disableOthers(item)"/>
          </v-col>
        </v-row>
      </div>
      <div v-else>
        {{ item.endRule }}
      </div>
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
  </n-n-table>
  <study-visits-duplicate-form
    :open="duplicateForm"
    @close="closeDuplicateForm"
    :studyVisit="selectedStudyVisit" />
  <v-dialog
    v-model="showForm"
    persistent
    max-width="1200px"
    content-class="top-dialog"
    >
    <study-visit-form :opened="showForm" :firstVisit="studyVisits ? (studyVisits.length === 0) : true" :studyVisit="selectedStudyVisit" @close="closeForm" />
  </v-dialog>
  <v-dialog v-model="showHistory">
    <history-table @close="closeHistory" type="studyVisit" url-prefix="/studies/" :item="selectedStudyVisit" :title-label="$t('StudyVisitTimeline.history_title')"/>
  </v-dialog>
  <v-dialog v-model="showStudyVisitsHistory">
    <summary-history-table @close="closeStudyVisitsHistory" type="studyVisits" :title-label="$t('StudyDesignTable.study_visits')" />
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import { bus } from '@/main'
import { mapGetters } from 'vuex'
import units from '@/api/units'
import terms from '@/api/controlledTerminology/terms'
import ActionsMenu from '@/components/tools/ActionsMenu'
import NNTable from '@/components/tools/NNTable'
import StudyVisitForm from './StudyVisitForm'
import HorizontalBarChart from '@/components/tools/HorizontalBarChart'
import BubbleChart from '@/components/tools/BubbleChart'
import HistoryTable from '@/components/library/HistoryTable'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import visitConstants from '@/constants/visits'
import filteringParameters from '@/utils/filteringParameters'
import StudyVisitsDuplicateForm from './StudyVisitsDuplicateForm'
import SummaryHistoryTable from '@/components/tools/SummaryHistoryTable'

export default {
  components: {
    ConfirmDialog,
    ActionsMenu,
    NNTable,
    StudyVisitForm,
    HorizontalBarChart,
    BubbleChart,
    HistoryTable,
    StudyVisitsDuplicateForm,
    SummaryHistoryTable
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyEpochs: 'studyEpochs/studyEpochs',
      studyVisits: 'studyEpochs/studyVisits'
    }),
    barChartStyles () {
      return {
        position: 'relative',
        height: '200px'
      }
    },
    lineChartStyles () {
      return {
        position: 'relative',
        height: '90px'
      }
    },
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-visits`
    },
    singleStudyVisits () {
      return this.studyVisits.filter(visit => visit.visitClass === visitConstants.CLASS_SINGLE_VISIT)
    }
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'edit') && !this.editMode,
          click: this.editVisit
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => item.possibleActions.find(action => action === 'delete') && !this.editMode,
          click: this.deleteVisit
        },
        {
          label: this.$t('StudyVisitTable.duplicate'),
          icon: 'mdi-plus-box-multiple-outline',
          iconColor: 'primary',
          condition: (item) => item && !this.editMode,
          click: this.openDuplicateForm
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          condition: (item) => item.visitClass === 'SINGLE_VISIT' && !this.editMode,
          click: this.openVisitHistory
        },
        {
          label: this.$t('_global.save'),
          condition: (item) => item && this.editMode,
          icon: 'mdi-content-save',
          click: this.saveVisit
        },
        {
          label: this.$t('_global.cancel'),
          condition: (item) => item && this.editMode,
          icon: 'mdi-close-thick',
          click: this.cancelVisitEditing
        }
      ],
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyVisitForm.study_epoch'), value: 'studyEpochUid' },
        { text: this.$t('StudyVisitForm.visit_type'), value: 'visitTypeName' },
        { text: this.$t('StudyVisitForm.visit_class'), value: 'visitClass' },
        { text: this.$t('StudyVisitForm.anchor_visit_in_group'), value: 'visitSubclass' },
        { text: this.$t('StudyVisitForm.visit_group'), value: 'visitSubName' },
        { text: this.$t('StudyVisitForm.global_anchor_visit'), value: 'isGlobalAnchorVisit' },
        { text: this.$t('StudyVisitForm.contact_mode'), value: 'visitContactModeName' },
        { text: this.$t('StudyVisitForm.time_reference'), value: 'timeReferenceName' },
        { text: this.$t('StudyVisitForm.time_value'), value: 'timeValue' },
        { text: this.$t('StudyVisitForm.visit_number'), value: 'order' },
        { text: this.$t('StudyVisitForm.unique_visit_number'), value: 'uniqueVisitNumber' },
        { text: this.$t('StudyVisitForm.visit_name'), value: 'visitName' },
        { text: this.$t('StudyVisitForm.visit_short_name'), value: 'visitShortName' },
        { text: this.$t('StudyVisitForm.study_day_label'), value: 'studyDayLabel' },
        { text: this.$t('StudyVisitForm.study_week_label'), value: 'studyWeekLabel' },
        { text: this.$t('StudyVisitForm.visit_window'), value: 'visitWindow' },
        { text: this.$t('StudyVisitForm.consecutive_visit'), value: 'consecutiveVisitGroup' },
        { text: this.$t('StudyVisitForm.show_wisit'), value: 'showVisit' },
        { text: this.$t('StudyVisitForm.visit_description'), value: 'description' },
        { text: this.$t('StudyVisitForm.epoch_allocation'), value: 'epochAllocationName' },
        { text: this.$t('StudyVisitForm.visit_start_rule'), value: 'startRule' },
        { text: this.$t('StudyVisitForm.visit_stop_rule'), value: 'endRule' },
        { text: this.$t('_global.modified'), value: 'modifiedDate' },
        { text: this.$t('StudyVisitForm.modified_user'), value: 'userInitials' }
      ],
      defaultColumns: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyVisitForm.study_epoch'), value: 'studyEpochUid' },
        { text: this.$t('StudyVisitForm.visit_type'), value: 'visitTypeName' },
        { text: this.$t('StudyVisitForm.visit_class'), value: 'visitClass' },
        { text: this.$t('StudyVisitForm.anchor_visit_in_group'), value: 'visitSubclass' },
        { text: this.$t('StudyVisitForm.visit_group'), value: 'visitSubName' },
        { text: this.$t('StudyVisitForm.global_anchor_visit'), value: 'isGlobalAnchorVisit' },
        { text: this.$t('StudyVisitForm.contact_mode'), value: 'visitContactModeName' },
        { text: this.$t('StudyVisitForm.time_reference'), value: 'timeReferenceName' },
        { text: this.$t('StudyVisitForm.time_value'), value: 'timeValue' },
        { text: this.$t('StudyVisitForm.visit_number'), value: 'order' },
        { text: this.$t('StudyVisitForm.unique_visit_number'), value: 'uniqueVisitNumber' },
        { text: this.$t('StudyVisitForm.visit_name'), value: 'visitName' },
        { text: this.$t('StudyVisitForm.visit_short_name'), value: 'visitShortName' },
        { text: this.$t('StudyVisitForm.study_day_label'), value: 'studyDayLabel' },
        { text: this.$t('StudyVisitForm.study_week_label'), value: 'studyWeekLabel' },
        { text: this.$t('StudyVisitForm.visit_window'), value: 'visitWindow' },
        { text: this.$t('StudyVisitForm.consecutive_visit'), value: 'consecutiveVisitGroup' },
        { text: this.$t('StudyVisitForm.show_wisit'), value: 'showVisit' },
        { text: this.$t('StudyVisitForm.visit_description'), value: 'description' },
        { text: this.$t('StudyVisitForm.epoch_allocation'), value: 'epochAllocationName' },
        { text: this.$t('StudyVisitForm.visit_start_rule'), value: 'startRule' },
        { text: this.$t('StudyVisitForm.visit_stop_rule'), value: 'endRule' },
        { text: this.$t('_global.modified'), value: 'modifiedDate' },
        { text: this.$t('StudyVisitForm.modified_user'), value: 'userInitials' }
      ],
      editHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyVisitForm.visit_type'), value: 'visitTypeName' },
        { text: this.$t('StudyVisitForm.global_anchor_visit'), value: 'isGlobalAnchorVisit' },
        { text: this.$t('StudyVisitForm.contact_mode'), value: 'visitContactModeName' },
        { text: this.$t('StudyVisitForm.time_reference'), value: 'timeReferenceName' },
        { text: this.$t('StudyVisitForm.time_value'), value: 'timeValue' },
        { text: this.$t('StudyVisitForm.visit_name'), value: 'visitName' },
        { text: this.$t('StudyVisitForm.visit_window'), value: 'visitWindow' },
        { text: this.$t('StudyVisitForm.show_wisit'), value: 'showVisit' },
        { text: this.$t('StudyVisitForm.visit_description'), value: 'description' },
        { text: this.$t('StudyVisitForm.visit_start_rule'), value: 'startRule' },
        { text: this.$t('StudyVisitForm.visit_stop_rule'), value: 'endRule' }
      ],
      selectedStudyVisit: null,
      showForm: false,
      showHistory: false,
      timeUnits: [],
      loading: true,
      barChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        tooltips: {
          enabled: false
        },
        interaction: {
          intersect: false
        },
        scales: {
          xAxes: [{
            ticks: {
              display: false,
              max: 0,
              min: 0
            },
            gridLines: {
              display: false,
              color: '#fff',
              zeroLineColor: '#fff',
              zeroLineWidth: 0
            },
            stacked: false
          }],
          yAxes: [{
            stacked: true
          }]
        },
        indexAxis: 'y'
      },
      lineChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        legend: {
          display: false
        },
        tooltips: {
          callbacks: {
            label: function (tooltipItem, data) {
              return [[data.datasets[tooltipItem.datasetIndex].label, ` ${data.datasets[tooltipItem.datasetIndex].contactMode}`], [data.datasets[tooltipItem.datasetIndex].visitType, ` Day ${data.datasets[tooltipItem.datasetIndex].studyDay}`, ` ${data.datasets[tooltipItem.datasetIndex].week}`]]
            }
          },
          backgroundColor: 'rgba(226, 230, 240, 0.8)',
          bodyFontColor: '#000',
          displayColors: false,
          bodyFontSize: 15
        },
        interaction: {
          mode: 'dataset'
        },
        scales: {
          yAxes: [{
            gridLines: {
              display: false,
              color: '#fff',
              zeroLineColor: '#fff',
              zeroLineWidth: 0
            },
            ticks: {
              display: false
            }
          }],
          xAxes: [{
            ticks: {
              max: 0,
              min: 1,
              stepSize: 7,
              precision: 0
            },
            scaleLabel: {
              display: true,
              labelString: this.$t('StudyVisitTable.study_day')
            }
          }]
        },
        indexAxis: 'y'
      },
      barChartDatasets: {
        datasets: []
      },
      lineChartDatasets: {
        datasets: []
      },
      chartsKey: 0,
      barChartKey: 0,
      options: {},
      duplicateForm: false,
      editMode: false,
      contactModes: [],
      itemsDisabled: false,
      visitClasses: [
        { label: this.$t('StudyVisitForm.scheduled_visit'), value: visitConstants.CLASS_SINGLE_VISIT },
        { label: this.$t('StudyVisitForm.unscheduled_visit'), value: visitConstants.CLASS_UNSCHEDULED_VISIT },
        { label: this.$t('StudyVisitForm.non_visit'), value: visitConstants.CLASS_NON_VISIT }
      ],
      timeReferences: [],
      showStudyVisitsHistory: false
    }
  },
  methods: {
    openStudyVisitsHistory () {
      this.showStudyVisitsHistory = true
    },
    closeStudyVisitsHistory () {
      this.showStudyVisitsHistory = false
    },
    openEditMode () {
      this.headers = this.editHeaders
      this.editMode = true
    },
    closeEditMode () {
      this.$store.dispatch('studyEpochs/fetchStudyVisits', this.selectedStudy.uid)
      this.editMode = false
      this.headers = this.defaultColumns
    },
    disableOthers (item) {
      if (item.minVisitWindowValue > 0) {
        item.minVisitWindowValue = item.minVisitWindowValue * -1
      }
      if (!this.itemsDisabled) {
        this.studyVisits.forEach(visit => {
          this.$set(visit, 'disabled', visit.uid !== item.uid)
        })
        this.itemsDisabled = true
      }
    },
    saveVisit (item) {
      return this.$store.dispatch('studyEpochs/updateStudyVisit', { studyUid: this.selectedStudy.uid, studyVisitUid: item.uid, input: item }).then(resp => {
        this.$store.dispatch('studyEpochs/fetchStudyVisits', this.selectedStudy.uid)
        bus.$emit('notification', { msg: this.$t('StudyVisitForm.update_success') })
        this.itemsDisabled = false
      })
    },
    cancelVisitEditing () {
      this.$store.dispatch('studyEpochs/fetchStudyVisits', this.selectedStudy.uid)
      this.itemsDisabled = false
    },
    edit () {
      this.editMode = true
    },
    openDuplicateForm (item) {
      this.selectedStudyVisit = item
      this.duplicateForm = true
    },
    closeDuplicateForm () {
      this.selectedStudyVisit = null
      this.duplicateForm = false
    },
    fetchStudyVisits (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.studyUid = this.selectedStudy.uid
      this.$store.dispatch('studyEpochs/fetchFilteredStudyVisits', params)
    },
    getDisplay (item, name) {
      if (name in this.calculatedItems) {
        return this.calculatedItems[name][item[name]]._displayValue
      } else {
        return item[name]
      }
    },
    createMapping (codelist, param, displayValue) {
      const returnValue = {}
      codelist.forEach(item => {
        item._displayValue = item[displayValue]
        returnValue[item[param]] = item
      })
      return returnValue
    },
    editVisit (item) {
      this.selectedStudyVisit = item
      this.showForm = true
    },
    async openForm () {
      if (this.studyEpochs.length === 0) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('StudyVisitForm.add_epoch'),
          redirect: 'epochs'
        }
        if (!await this.$refs.confirm.open(this.$t('StudyVisitForm.create_epoch'), options)) {
          return
        }
      }
      this.showForm = true
    },
    closeForm () {
      this.selectedStudyVisit = null
      this.showForm = false
    },
    async deleteVisit (item) {
      await this.$store.dispatch('studyEpochs/deleteStudyVisit', { studyUid: this.selectedStudy.uid, studyVisitUid: item.uid })
      bus.$emit('notification', { msg: this.$t('StudyVisitTable.delete_success') })
      await this.$store.dispatch('studyEpochs/fetchStudyVisits', this.selectedStudy.uid)
    },
    openVisitHistory (item) {
      this.selectedStudyVisit = item
      this.showHistory = true
    },
    closeHistory () {
      this.selectedStudyVisit = null
      this.showHistory = false
    },
    getStudyEpochName (studyEpochUid) {
      if (this.studyEpochs) {
        const epoch = this.studyEpochs.find(item => item.uid === studyEpochUid)
        return epoch.epochName
      }
      return ''
    },
    getUnitName (unitUid) {
      const unit = this.timeUnits.find(item => item.uid === unitUid)
      if (unit) {
        return unit.name
      }
      return ''
    },
    buildChart () {
      this.loading = true
      this.barChartDatasets.datasets = []
      this.lineChartDatasets.datasets = []
      const negativeDaysEpochs = []
      let maxDay = 0
      for (const d of this.studyEpochs) {
        if (d.startDay >= 0) {
          break
        } else {
          negativeDaysEpochs.push(d)
        }
      }
      this.studyEpochs.splice(0, negativeDaysEpochs.length) // Reordering of the epochs with visit with the negative day number
      negativeDaysEpochs.forEach(el => { //  needed for correct timeline display
        this.studyEpochs.unshift(el)
      })
      this.studyEpochs.forEach(el => {
        if (el.epochName !== visitConstants.EPOCH_BASIC) {
          if (el.endDay > maxDay) {
            maxDay = el.endDay
          }
          this.barChartDatasets.datasets.push(
            {
              data: [[el.startDay, el.endDay]],
              backgroundColor: el.colorHash, // and for the rest we need to just provide duration of epoch, but if the first epoch has positive first day number than we need to build
              label: el.epochName // such array just for the first epoch
            }
          )
        }
      })
      this.singleStudyVisits.forEach(el => {
        this.lineChartDatasets.datasets.push(
          {
            data: [{
              x: el.studyDayNumber,
              y: 0,
              r: 7
            }],
            studyDay: el.studyDayNumber,
            label: el.visitName,
            backgroundColor: 'rgb(6, 57, 112)',
            contactMode: el.visitContactModeName,
            visitType: el.visitTypeName,
            week: el.studyWeekLabel
          }
        )
      })
      if (this.singleStudyVisits.length > 0) {
        const lastVisitDay = this.singleStudyVisits[this.singleStudyVisits.length - 1].studyDayNumber
        const firstVisitDay = this.singleStudyVisits[0].studyDayNumber

        this.barChartOptions.scales.xAxes[0].ticks.max = Math.round(maxDay)
        this.lineChartOptions.scales.xAxes[0].ticks.max = Math.round(maxDay)
        this.barChartOptions.scales.xAxes[0].ticks.min = (firstVisitDay < 0) ? Math.round(firstVisitDay) - 1 : Math.round(firstVisitDay)
        this.lineChartOptions.scales.xAxes[0].ticks.min = (firstVisitDay < 0) ? Math.round(firstVisitDay) - 1 : Math.round(firstVisitDay)
        this.lineChartOptions.scales.xAxes[0].ticks.stepSize = 7 * Math.ceil(lastVisitDay / 100)
      }
      this.loading = false
      this.chartsKey += 1
      this.barChartKey += 1
    }
  },
  mounted () {
    this.calculatedItems = {}
    terms.getByCodelist('timepointReferences').then(resp => {
      this.calculatedItems.timeReferenceUid = this.createMapping(resp.data.items, 'termUid', 'sponsorPreferredName')
      terms.getByCodelist('epochs').then(resp => {
        this.calculatedItems.epochUid = this.createMapping(resp.data.items, 'termUid', 'sponsorPreferredName')
      })
    })
    this.$store.dispatch('studyEpochs/fetchStudyEpochs', this.selectedStudy.uid).then(() => {
      this.$store.dispatch('studyEpochs/fetchStudyVisits', this.selectedStudy.uid).then(() => {
      })
    })
    units.getBySubset('Study Time').then(resp => {
      this.timeUnits = resp.data.items
    })
    terms.getByCodelist('contactModes').then(resp => {
      this.contactModes = resp.data.items
    })
    terms.getByCodelist('timepointReferences').then(resp => {
      this.timeReferences = resp.data.items
    })
  },
  watch: {
    studyVisits () {
      this.buildChart()
    }
  }
}
</script>

<style scoped>
  .cellWidth {
    width: 200px;
  }
</style>
