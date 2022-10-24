<template>
<div class="pa-4">
  <div class="d-flex align-center mb-4">
    <v-radio-group
      v-model="expandAllRows"
      row
      hide-details
      @change="toggleAllRowState"
      >
      <v-radio
        :label="$t('DetailedFlowchart.expand_all')"
        :value="true"
        />
      <v-radio
        :label="$t('DetailedFlowchart.collapse_all')"
        :value="false"
        />
    </v-radio-group>
    <v-spacer />
    <v-btn
      fab
      small
      color="primary"
      @click="openBatchForm()"
      :title="$t('StudyActivityInstructionTable.open_batch_form')"
      >
      <v-icon>
        mdi-plus-box-multiple
      </v-icon>
    </v-btn>
  </div>
  <table>
    <thead>
      <tr>
        <th width="5%"></th>
        <th width="25%">{{ $t('StudyActivityInstructionTable.activities') }}</th>
        <th width="15%">{{ $t('StudyActivityInstructionTable.visits') }}</th>
        <th width="50%">{{ $t('StudyActivityInstructionTable.instructions') }}</th>
        <th width="5%"></th>
      </tr>
    </thead>
    <tbody>
      <template v-for="(groups, flowchartGroup, flGroupIndex) in sortedStudyActivities">
        <tr :key="flowchartGroup" class="flowchart text-uppercase">
          <td>
            <v-btn
              icon
              @click="toggleRowState(`flgroup-${flGroupIndex}`)"
              >
              <v-icon>{{ getDisplayButtonIcon(`flgroup-${flGroupIndex}`) }}</v-icon>
            </v-btn>
          </td>
          <td colspan="4" class="text-strong">{{ flowchartGroup }}</td>
        </tr>
        <template v-for="(subgroups, group, groupIndex) in groups">
          <template v-if="rowsDisplayState[`flgroup-${flGroupIndex}`]">
            <tr :key="`${flowchartGroup}-${group}`" class="group">
              <td>
                <v-btn
                  icon
                  @click="toggleRowState(`group-${flGroupIndex}-${groupIndex}`)"
                  >
                  <v-icon>{{ getDisplayButtonIcon(`group-${flGroupIndex}-${groupIndex}`) }}</v-icon>
                </v-btn>
              </td>
              <td colspan="4" class="text-strong">{{ group }}</td>
            </tr>
            <template v-for="(studyActivities, subgroup, subgroupIndex) in subgroups">
              <template v-if="rowsDisplayState[`group-${flGroupIndex}-${groupIndex}`]">
                <tr :key="`${flowchartGroup}-${group}-${subgroup}`">
                  <td>
                    <v-btn
                      icon
                      @click="toggleRowState(`subgroup-${flGroupIndex}-${groupIndex}-${subgroupIndex}`)"
                      >
                      <v-icon>{{ getDisplayButtonIcon(`subgroup-${flGroupIndex}-${groupIndex}-${subgroupIndex}`) }}</v-icon>
                    </v-btn>
                  </td>
                  <td colspan="4" class="subgroup">
                    <div class="d-flex align-center">
                      <v-checkbox
                        @change="value => toggleSubgroupActivitiesSelection(flowchartGroup, group, subgroup, value)"
                        on-icon="mdi-checkbox-multiple-marked"
                        off-icon="mdi-checkbox-multiple-blank-outline"
                        hide-details
                        />
                      {{ subgroup }}
                    </div>
                  </td>
                </tr>
                <template v-if="rowsDisplayState[`subgroup-${flGroupIndex}-${groupIndex}-${subgroupIndex}`]">
                  <tr v-for="studyActivity in studyActivities" :key="studyActivity.studyActivityUid">
                    <td></td>
                    <td class="activity">
                      <div class="d-flex align-center">
                        <v-checkbox
                          hide-details
                          @change="value => toggleActivitySelection(studyActivity, value)"
                          :value="currentSelection.findIndex(item => item.studyActivityUid === studyActivity.studyActivityUid) !== -1"
                          />
                        {{ studyActivity.activity.name }}
                      </div>
                    </td>
                    <td>{{ getStudyActivityVisits(studyActivity.studyActivityUid) }}</td>
                    <td>
                      <n-n-parameter-highlighter
                        :name="getStudyActivityInstruction(studyActivity.studyActivityUid)"
                        :show-prefix-and-postfix="false"
                        />
                    </td>
                    <td>
                      <actions-menu
                        v-if="getStudyActivityInstruction(studyActivity.studyActivityUid)"
                        :actions="actions"
                        :item="studyActivity"
                        />
                    </td>
                  </tr>
                </template>
              </template>
            </template>
          </template>
        </template>
      </template>
    </tbody>
  </table>
  <v-dialog
    v-model="showBatchForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
    >
    <study-activity-instruction-batch-form
      :study-activities="currentSelection"
      :current-study-activity-instructions="studyActivityInstructions"
      @close="closeBatchForm"
      class="fullscreen-dialog"
      @added="getInstructionsPerActivity"
      />
  </v-dialog>
  <v-dialog
    v-model="showBatchEditForm"
    persistent
    content-class="top-dialog"
    max-width="800px"
    >
    <study-activity-instruction-batch-edit-form
      :selection="currentSelection"
      :instructions-per-study-activity="instructionsPerStudyActivity"
      :open="showBatchEditForm"
      @close="closeBatchEditForm"
      @deleted="onInstructionsDeleted"
      @updated="getInstructionsPerActivity"
      />
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu'
import { bus } from '@/main'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import { mapGetters } from 'vuex'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import study from '@/api/study'
import StudyActivityInstructionBatchForm from './StudyActivityInstructionBatchForm'
import StudyActivityInstructionBatchEditForm from './StudyActivityInstructionBatchEditForm'
import studyEpochs from '@/api/studyEpochs'

export default {
  components: {
    ActionsMenu,
    ConfirmDialog,
    NNParameterHighlighter,
    StudyActivityInstructionBatchEditForm,
    StudyActivityInstructionBatchForm
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      sortedStudyActivities: 'studyActivities/sortedStudyActivities'
    })
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editActivityInstruction
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteActivityInstruction
        }
      ],
      currentSelection: [],
      expandAllRows: false,
      instructionsPerStudyActivity: {},
      rowsDisplayState: {},
      showBatchForm: false,
      showBatchEditForm: false,
      studyActivityInstructions: [],
      visitsPerStudyActivity: {}
    }
  },
  methods: {
    getCurrentDisplayValue (rowKey) {
      const currentValue = this.rowsDisplayState[rowKey]
      if (currentValue === undefined) {
        return false
      }
      return currentValue
    },
    getDisplayButtonIcon (rowKey) {
      return (this.getCurrentDisplayValue(rowKey)) ? 'mdi-chevron-up' : 'mdi-chevron-down'
    },
    async getInstructionsPerActivity () {
      this.instructionsPerStudyActivity = {}
      const resp = await study.getStudyActivityInstructions(this.selectedStudy.uid)
      for (const instruction of resp.data) {
        this.$set(this.instructionsPerStudyActivity, instruction.studyActivityUid, instruction)
      }
      this.studyActivityInstructions = resp.data
    },
    getStudyActivityInstruction (studyActivityUid) {
      if (this.instructionsPerStudyActivity[studyActivityUid] !== undefined) {
        return this.instructionsPerStudyActivity[studyActivityUid].activityInstructionName
      }
      return ''
    },
    async getVisitsPerActivity () {
      const resp = await studyEpochs.getStudyVisits(this.selectedStudy.uid)
      const visitNamePerUid = {}

      for (const visit of resp.data.items) {
        visitNamePerUid[visit.uid] = visit.visitShortName
      }
      study.getStudyActivitySchedules(this.selectedStudy.uid).then(resp => {
        for (const schedule of resp.data) {
          if (this.visitsPerStudyActivity[schedule.studyActivityUid] === undefined) {
            this.$set(this.visitsPerStudyActivity, schedule.studyActivityUid, [])
          }
          this.visitsPerStudyActivity[schedule.studyActivityUid].push(visitNamePerUid[schedule.studyVisitUid])
        }
      })
    },
    getStudyActivityVisits (studyActivityUid) {
      if (this.visitsPerStudyActivity[studyActivityUid] === undefined) {
        return ''
      }
      return this.visitsPerStudyActivity[studyActivityUid].join(', ')
    },
    editActivityInstruction (studyActivityInstruction) {
      this.currentSelection = [studyActivityInstruction]
      this.showBatchEditForm = true
    },
    async deleteActivityInstruction (studyActivity) {
      const options = { type: 'warning' }
      const instruction = this.instructionsPerStudyActivity[studyActivity.studyActivityUid]
      const uid = instruction.studyActivityInstructionUid
      const msg = this.$t('StudyActivityInstructionTable.confirm_delete', { instruction: instruction.activityInstructionName })
      if (await this.$refs.confirm.open(msg, options)) {
        study.deleteStudyActivityInstruction(this.selectedStudy.uid, uid).then(resp => {
          this.$delete(this.instructionsPerStudyActivity, studyActivity.studyActivityUid)
          bus.$emit('notification', { type: 'success', msg: this.$t('StudyActivityInstructionTable.delete_success') })
        })
      }
    },
    /*
    ** Event handler to update display after some instructions were batch deleted
    */
    onInstructionsDeleted () {
      for (const item of this.currentSelection) {
        this.$delete(this.instructionsPerStudyActivity, item.studyActivityUid)
      }
    },
    openBatchForm () {
      if (!this.currentSelection.length) {
        bus.$emit('notification', { type: 'warning', msg: this.$t('StudyActivityInstructionTable.batch_no_selection') })
        return
      }
      let itemWithNoInstruction = false
      for (const item of this.currentSelection) {
        if (this.instructionsPerStudyActivity[item.studyActivityUid] === undefined) {
          itemWithNoInstruction = true
          break
        }
      }
      if (itemWithNoInstruction) {
        this.showBatchForm = true
      } else {
        this.showBatchEditForm = true
      }
    },
    closeBatchForm () {
      this.showBatchForm = false
    },
    closeBatchEditForm () {
      this.showBatchEditForm = false
      this.currentSelection = []
    },
    toggleRowState (rowKey) {
      const currentValue = this.getCurrentDisplayValue(rowKey)
      this.$set(this.rowsDisplayState, rowKey, !currentValue)
    },
    toggleAllRowState (value) {
      let flgroupIndex = 0
      for (const flgroup in this.sortedStudyActivities) {
        let groupIndex = 0
        this.$set(this.rowsDisplayState, `flgroup-${flgroupIndex}`, value)
        for (const group in this.sortedStudyActivities[flgroup]) {
          let subgroupIndex = 0
          this.$set(this.rowsDisplayState, `group-${flgroupIndex}-${groupIndex}`, value)
          for (const subgroup in this.sortedStudyActivities[flgroup][group]) { // eslint-disable-line no-unused-vars
            this.$set(this.rowsDisplayState, `subgroup-${flgroupIndex}-${groupIndex}-${subgroupIndex}`, value)
            subgroupIndex += 1
          }
          groupIndex += 1
        }
        flgroupIndex += 1
      }
    },
    toggleActivitySelection (studyActivity, value) {
      if (value) {
        this.currentSelection.push(studyActivity)
      } else {
        for (let i = 0; i < this.currentSelection.length; i++) {
          if (this.currentSelection[i].studyActivityUid === studyActivity.studyActivityUid) {
            this.currentSelection.splice(i, 1)
            break
          }
        }
      }
    },
    toggleSubgroupActivitiesSelection (flgroup, group, subgroup, value) {
      if (value) {
        this.currentSelection = this.currentSelection.concat(this.sortedStudyActivities[flgroup][group][subgroup])
      } else {
        for (const studyActivity of this.sortedStudyActivities[flgroup][group][subgroup]) {
          const index = this.currentSelection.findIndex(item => item.studyActivityUid === studyActivity.studyActivityUid)
          this.currentSelection.splice(index, 1)
        }
      }
    }
  },
  mounted () {
    this.$store.dispatch('studyActivities/fetchStudyActivities', { studyUid: this.selectedStudy.uid })
    this.getVisitsPerActivity()
    this.getInstructionsPerActivity()
  }
}
</script>

<style scoped lang="scss">
table {
  width: 100%;
  text-align: left;
  border-spacing: 0px;
  border-collapse: collapse;
}
thead {
  background-color: var(--v-greyBackground-base);
  font-weight: 600;
}
tr {
  padding: 4px;
  &.section {
    background-color: var(--v-greyBackground-base);
    font-weight: 600;
  }
}
tbody tr {
  border-bottom: 1px solid var(--v-greyBackground-base);
}
th {
  vertical-align: middle;
  padding-top: 16px !important;
  padding-bottom: 16px !important;
}
th, td {
  padding: 6px;
  font-size: 14px !important;
}
.flowchart {
  background-color: var(--v-dfltBackgroundLight1-base);

}
.group {
  background-color: var(--v-dfltBackgroundLight2-base);
}
.subgroup {
  font-weight: 600;
  padding-left: 20px;
}
.activity {
  padding-left: 20px;
}
.text-vertical {
  writing-mode: vertical-rl;
  text-orientation: mixed;
}
.text-strong {
  font-weight: 600;
}
</style>
