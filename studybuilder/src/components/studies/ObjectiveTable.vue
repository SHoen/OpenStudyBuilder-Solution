<template>
<div>
  <n-n-table
    key="objectiveTable"
    :headers="headers"
    :items="studyObjectives"
    item-key="studyObjectiveUid"
    has-api
    :column-data-resource="`study/${selectedStudy.uid}/study-objectives`"
    export-object-label="StudyObjectives"
    :export-data-url="exportDataUrl"
    has-history
    :options.sync="options"
    :server-items-length="total"
    @filter="fetchObjectives"
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
    <template v-slot:actions>
      <v-btn
        data-cy="add-study-objective"
        fab
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('StudyObjectiveForm.add_title')"
        >
        <v-icon>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:body="props" v-if="sortMode">
      <draggable
        :list="props.items"
        tag="tbody"
        :move="checkObjectiveLevel"
        @change="onOrderChange($event)"
        >
        <tr
          v-for="(item, index) in props.items"
          :key="index"
          >
          <td v-if="props.showSelectBoxes">
            <v-checkbox
              :value="item.objective.name"
              hide-details
              @change="props.select(!props.isSelected(item))"
              />
          </td>
          <td>
            <actions-menu :actions="actions" :item="item" />
          </td>
          <td>
            <v-icon
              small
              class="page__grab-icon"
              >
              mdi-sort
            </v-icon>
            {{ item.order }}
          </td>
          <td v-if="item.objectiveLevel">{{ item.objectiveLevel.sponsorPreferredName }}</td>
          <td v-else></td>
          <td>
            <n-n-parameter-highlighter
              :name="item.objective.name"
              :show-prefix-and-postfix="false"
              />
          </td>
          <td>{{ item.endpointCount }}</td>
          <td>{{ item.startDate | date }}</td>
          <td>{{ item.userInitials }}</td>
        </tr>
      </draggable>
    </template>
    <template v-slot:item.objective.name="{ item }">
      <n-n-parameter-highlighter
        :name="item.objective.name"
        :show-prefix-and-postfix="false"
        />
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate | date }}
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu
        :actions="actions"
        :item="item"
        :badge="actionsMenuBadge(item)"
        />
    </template>
  </n-n-table>
  <v-dialog v-model="showForm"
            persistent
            fullscreen
            content-class="fullscreen-dialog"
            >
    <objective-form
      @close="closeForm"
      :current-study-objectives="studyObjectives"
      :study-objective="selectedObjective"
      class="fullscreen-dialog"
      />
  </v-dialog>
  <v-dialog v-model="showHistory"
            persistent
            max-width="1200px">
    <history-table
      @close="closeHistory"
      :type="'studyObjective'"
      :item="selectedStudyObjective"
      :title-label="'Study Objective'"
      :headers="historyHeaders"
      />
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-snackbar
    v-model="snackbar"
    color="error"
    top
    >
    <v-icon class="mr-2">mdi-alert</v-icon>
    {{ $t('StudyObjectivesTable.sort_help_msg') }}
  </v-snackbar>
</div>
</template>

<script>
import draggable from 'vuedraggable'
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import study from '@/api/study'
import ActionsMenu from '@/components/tools/ActionsMenu'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import ObjectiveForm from '@/components/studies/ObjectiveForm'
import HistoryTable from '@/components/library/HistoryTable'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import statuses from '@/constants/statuses'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    draggable,
    NNParameterHighlighter,
    ObjectiveForm,
    HistoryTable,
    NNTable,
    ConfirmDialog
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyObjectives: 'studyObjectives/studyObjectives'
    }),
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-objectives`
    }
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('StudyObjectivesTable.update_version_retired_tooltip'),
          icon: 'mdi-alert',
          iconColor: 'orange',
          condition: (item) => this.isLatestRetired(item)
        },
        {
          label: this.$t('StudyObjectivesTable.update_version_tooltip'),
          icon: 'mdi-bell-ring',
          iconColorFunc: this.objectiveUpdateAborted,
          condition: this.needUpdate,
          click: this.updateVersion
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editObjective
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteStudyObjective
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory
        }
      ],
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyObjectivesTable.order'), value: 'order', width: '3%' },
        {
          text: this.$t('StudyObjectivesTable.objective_level'),
          value: 'objectiveLevel.sponsorPreferredName'
        },
        { text: this.$t('_global.objective'), value: 'objective.name', width: '30%' },
        { text: this.$t('StudyObjectivesTable.endpoint_count'), value: 'endpointCount' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: 'userInitials' }
      ],
      historyHeaders: [
        { text: this.$t('StudyObjectivesTable.objective'), value: 'objective.name' },
        { text: this.$t('StudyObjectivesTable.objective_level'), value: 'objectiveLevel.sponsorPreferredName' },
        { text: this.$t('StudyObjectivesTable.order'), value: 'order' },
        { text: this.$t('HistoryTable.change_description'), value: 'changeType' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.user'), value: 'userInitials' },
        { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
        { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
      ],
      selectedObjective: null,
      selectedStudyObjective: null,
      showForm: false,
      showModForm: false,
      snackbar: false,
      sortBy: 'objectiveLevel',
      showHistory: false,
      sortDesc: false,
      sortMode: false,
      abortConfirm: false,
      options: {},
      total: 0
    }
  },
  methods: {
    fetchObjectives (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.studyUid = this.selectedStudy.uid
      this.$store.dispatch('studyObjectives/fetchStudyObjectives', params).then(resp => {
        this.total = resp.data.total
      })
    },
    needUpdate (item) {
      if (item.latestObjective) {
        if (!this.isLatestRetired(item)) {
          return item.objective.version !== item.latestObjective.version
        }
      }
      return false
    },
    actionsMenuBadge (item) {
      if (this.needUpdate(item)) {
        return {
          color: 'error',
          icon: 'mdi-bell'
        }
      }
      return null
    },
    objectiveUpdateAborted (item) {
      return item.acceptedVersion ? '' : 'error'
    },
    isLatestRetired (item) {
      if (item.latestObjective) {
        return item.latestObjective.status === statuses.RETIRED
      }
      return false
    },
    async updateVersion (item) {
      const options = {
        type: 'warning',
        width: 1000,
        cancelLabel: this.$t('StudyObjectivesTable.keep_old_version'),
        agreeLabel: this.$t('StudyObjectivesTable.use_new_version')
      }
      const message = this.$t('StudyObjectivesTable.update_version_alert') + this.$t('StudyObjectivesTable.previous_version') + item.objective.name +
      ' ' + this.$t('StudyObjectivesTable.new_version') + ' ' + item.latestObjective.name

      if (await this.$refs.confirm.open(message, options)) {
        const args = {
          studyUid: item.studyUid,
          studyObjectiveUid: item.studyObjectiveUid
        }
        this.$store.dispatch('studyObjectives/updateStudyObjectiveLatestVersion', args).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyObjectivesTable.update_version_successful') })
        }).catch(error => {
          bus.$emit('notification', { type: 'error', msg: error.response.data.message })
        })
      } else {
        this.abortConfirm = true
        const args = {
          studyUid: item.studyUid,
          studyObjectiveUid: item.studyObjectiveUid
        }
        this.$store.dispatch('studyObjectives/updateStudyObjectiveAcceptVersion', args).then(resp => {
        }).catch(error => {
          bus.$emit('notification', { type: 'error', msg: error.response.data.message })
        })
      }
    },
    closeForm () {
      this.showForm = false
      this.selectedObjective = null
    },
    async deleteStudyObjective (studyObjective) {
      const options = { type: 'warning' }
      let objective = studyObjective.objective.name

      objective = objective.replaceAll(/\[|\]/g, '')
      if (await this.$refs.confirm.open(this.$t('StudyObjectivesTable.confirm_delete', { objective }), options)) {
        this.$store.dispatch('studyObjectives/deleteStudyObjective', {
          studyUid: this.selectedStudy.uid,
          studyObjectiveUid: studyObjective.studyObjectiveUid
        }).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyObjectivesTable.delete_objective_success') })
        })
      }
    },
    editObjective (objective) {
      this.selectedObjective = objective
      this.showForm = true
    },
    closeHistory () {
      this.selectedStudyObjective = null
      this.showHistory = false
    },
    openHistory (studyObjective) {
      this.selectedStudyObjective = studyObjective
      this.showHistory = true
    },
    /*
    ** Prevent dragging between different objective levels
    */
    checkObjectiveLevel (event) {
      const leftOrder = event.draggedContext.element.objectiveLevel ? event.draggedContext.element.objectiveLevel.order : null
      const rightOrder = event.relatedContext.element.objectiveLevel ? event.relatedContext.element.objectiveLevel.order : null
      const result = leftOrder === rightOrder
      this.snackbar = !result
      return result
    },
    onOrderChange (event) {
      const studyObjective = event.moved.element
      const replacedStudyObjective = this.studyObjectives[event.moved.newIndex]
      study.updateStudyObjectiveOrder(studyObjective.studyUid, studyObjective.studyObjectiveUid, replacedStudyObjective.order).then(resp => {
        this.$store.dispatch('studyObjectives/fetchStudyObjectives', { studyUid: this.selectedStudy.uid }).then(() => {
          this.sortStudyObjectives()
        })
      })
    },
    sortStudyObjectives () {
      this.studyObjectives.sort((a, b) => {
        return a.order - b.order
      })
    }
  },
  mounted () {
    this.$store.dispatch('studiesGeneral/fetchObjectiveLevels')
    this.fetchObjectives()
  },
  watch: {
    sortMode (value) {
      this.headers.forEach(header => {
        this.$set(header, 'sortable', !value)
      })
      this.sortStudyObjectives()
      if (value) {
        this.headers.unshift({ text: '', value: 'order', sortable: false, width: '5px' })
        this.sortBy = null
        this.sortStudyObjectives()
      } else {
        this.sortBy = null
        this.headers.splice(0, 1)
      }
    },
    studyObjectives (value) {
      if (value) {
        this.$emit('updated')
      }
    },
    options () {
      this.fetchObjectives()
    }
  }
}
</script>
