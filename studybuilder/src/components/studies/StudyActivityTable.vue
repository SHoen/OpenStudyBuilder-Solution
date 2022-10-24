<template>
<div>
  <n-n-table
    ref="table"
    :headers="headers"
    :items="studyActivities"
    :server-items-length="total"
    item-key="studyActivityUid"
    export-object-label="StudyActivities"
    :export-data-url="exportDataUrl"
    :options.sync="options"
    @filter="getStudyActivities"
    has-api
    :column-data-resource="`study/${selectedStudy.uid}/study-activities`"
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
    <template v-slot:actions="slot">
      <v-btn
        v-if="slot.showSelectBoxes"
        fab
        small
        color="primary"
        @click="openBatchEditForm(slot.selected)"
        :title="$t('StudyActivityTable.edit_activity_selection')"
        >
        <v-icon>
          mdi-pencil-box-multiple-outline
        </v-icon>
      </v-btn>
      <v-btn
        fab
        small
        class="ml-2"
        color="primary"
        @click.stop="showActivityForm = true"
        :title="$t('StudyActivityForm.add_title')"
        >
        <v-icon>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate|date }}
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu
        :actions="actions"
        :item="item"
        />
    </template>
    <template v-slot:body="props" v-if="sortMode">
      <draggable
        :list="props.items"
        tag="tbody"
        @change="onOrderChange($event)"
        >
        <tr
          v-for="(item, index) in props.items"
          :key="index"
          >
          <td v-if="props.showSelectBoxes">
            <v-checkbox
              :value="item.studyActivityUid"
              hide-details
              @change="props.select(!props.isSelected(item))"
              />
          </td>
          <td>
            <actions-menu
              :actions="actions"
              :item="item"
              />
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
          <td>{{ item.flowchartGroup.sponsorPreferredName }}</td>
          <td>{{ getActivityGroup(item) }}</td>
          <td>{{ getActivitySubGroup(item) }}</td>
          <td>{{ item.activity.name }}</td>
          <td>{{ item.note }}</td>
          <td>{{ item.startDate|date }}</td>
          <td>{{ item.userInitials }}</td>
        </tr>
      </draggable>
    </template>
  </n-n-table>
  <v-dialog
    v-model="showActivityForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
    >
    <study-activity-form
      @close="closeForm"
      @added="onStudyActivitiesUpdated"
      class="fullscreen-dialog"
      />
  </v-dialog>
  <v-dialog
    v-model="showActivityEditForm"
    max-width="1000px"
    >
    <study-activity-edit-form
      @close="closeEditForm"
      :study-activity="selectedStudyActivity"
      @updated="onStudyActivitiesUpdated"
      class="fullscreen-dialog"
      />
  </v-dialog>

  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog v-model="showHistory"
            persistent
            max-width="1200px">
    <history-table
      @close="closeHistory"
      type="studyActivity"
      :item="selectedStudyActivity"
      title-label="Study Activity"
      />
  </v-dialog>
  <study-activity-batch-edit-form
    :open="showBatchEditForm"
    :selection="currentSelection"
    @updated="onStudyActivitiesUpdated"
    @close="closeBatchEditForm"
    @remove="unselectItem"
    />
</div>
</template>

<script>
import { bus } from '@/main'
import draggable from 'vuedraggable'
import { mapGetters } from 'vuex'
import study from '@/api/study'
import ActionsMenu from '@/components/tools/ActionsMenu'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/library/HistoryTable'
import NNTable from '@/components/tools/NNTable'
import StudyActivityBatchEditForm from './StudyActivityBatchEditForm'
import StudyActivityEditForm from './StudyActivityEditForm'
import StudyActivityForm from './StudyActivityForm'

export default {
  components: {
    ActionsMenu,
    ConfirmDialog,
    draggable,
    HistoryTable,
    NNTable,
    StudyActivityBatchEditForm,
    StudyActivityEditForm,
    StudyActivityForm
  },
  computed: {
    ...mapGetters({
      studyActivities: 'studyActivities/studyActivities',
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-activities`
    }
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editStudyActivity
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteStudyActivity
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory
        }
      ],
      currentSelection: [],
      selectedStudyActivity: null,
      showActivityEditForm: false,
      showActivityForm: false,
      showBatchEditForm: false,
      showHistory: false,
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: '#', value: 'order', width: '5%' },
        { text: this.$t('StudyActivity.flowchart_group'), value: 'flowchartGroup.sponsorPreferredName' },
        { text: this.$t('StudyActivity.activity_group'), value: 'activity.activityGroup.name' },
        { text: this.$t('StudyActivity.activity_sub_group'), value: 'activity.activitySubGroup.name' },
        { text: this.$t('StudyActivity.activity'), value: 'activity.name' },
        { text: this.$t('StudyActivity.footnote'), value: 'note' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: 'userInitials' }
      ],
      sortMode: false,
      options: {},
      total: 0
    }
  },
  methods: {
    closeForm () {
      this.showActivityForm = false
    },
    closeEditForm () {
      this.showActivityEditForm = false
      this.selectedStudyActivity = null
    },
    async deleteStudyActivity (sa) {
      const options = { type: 'warning' }
      const activity = sa.activity.name
      const msg = (!sa.showActivityGroupInProtocolFlowchart || !sa.showActivitySubGroupInProtocolFlowchart)
        ? this.$t('StudyActivityTable.confirm_delete_side_effect')
        : this.$t('StudyActivityTable.confirm_delete', { activity })
      if (await this.$refs.confirm.open(msg, options)) {
        study.deleteStudyActivity(this.selectedStudy.uid, sa.studyActivityUid).then(resp => {
          this.getStudyActivities()
          bus.$emit('notification', { type: 'success', msg: this.$t('StudyActivityTable.delete_success') })
        })
      }
    },
    editStudyActivity (sa) {
      this.selectedStudyActivity = sa
      this.showActivityEditForm = true
    },
    openHistory (sa) {
      this.selectedStudyActivity = sa
      this.showHistory = true
    },
    closeHistory () {
      this.selectedStudyActivity = null
      this.showHistory = false
    },
    getStudyActivities (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.studyUid = this.selectedStudy.uid
      this.$store.dispatch('studyActivities/fetchStudyActivities', params).then(resp => {
        this.total = resp.data.total
      })
    },
    openBatchEditForm (selection) {
      if (!selection.length) {
        bus.$emit('notification', { type: 'warning', msg: this.$t('StudyActivityTable.batch_edit_no_selection') })
        return
      }
      this.currentSelection = selection
      this.showBatchEditForm = true
    },
    closeBatchEditForm () {
      this.currentSelection = []
      this.showBatchEditForm = false
    },
    onOrderChange (event) {
      const studyActivity = event.moved.element
      const replacedStudyActivity = this.studyActivities[event.moved.newIndex]
      study.updateStudyActivityOrder(studyActivity.studyUid, studyActivity.studyActivityUid, replacedStudyActivity.order).then(resp => {
        this.getStudyActivities()
      })
    },
    onStudyActivitiesUpdated () {
      this.getStudyActivities()
    },
    unselectItem (item) {
      this.currentSelection = this.currentSelection.filter(sa => sa.studyActivityUid !== item.studyActivityUid)
    }
  },
  mounted () {
    this.getStudyActivities()
  },
  watch: {
    options: {
      handler () {
        this.getStudyActivities()
      },
      deep: true
    }
  }
}
</script>
