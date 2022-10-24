<template>
<div class="pa-4" style="overflow-x: auto" v-resize="onResize">
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
    <v-switch
      v-model="hideFlowchartGroups"
      :label="$t('DetailedFlowchart.hide_flowchart_groups')"
      hide-details
      class="ml-2"
      />
    <v-spacer />
    <template v-if="!readOnly">
      <v-btn
        fab
        small
        @click="toggleActivitySelectionDisplay(false)"
        :title="$t('DetailedFlowchart.hide_activity_selection')"
        >
        <v-icon>
          mdi-eye-off-outline
        </v-icon>
      </v-btn>
      <v-btn
        fab
        small
        color="success"
        @click="toggleActivitySelectionDisplay(true)"
        :title="$t('DetailedFlowchart.show_activity_selection')"
        class="ml-2"
        >
        <v-icon>
          mdi-eye-outline
        </v-icon>
      </v-btn>
      <v-btn
        fab
        small
        color="primary"
        @click="openBatchEditForm"
        :title="$t('DetailedFlowchart.edit_activity_selection')"
        class="ml-2"
        >
        <v-icon>
          mdi-pencil-box-multiple-outline
        </v-icon>
      </v-btn>
    </template>
  </div>
  <div ref="tableContainer" class="sticky-header" :style="`height: ${tableHeight}px`">
  <table>
    <thead>
      <tr ref="firstHeader">
        <th width="2%" rowspan="4">
          <v-btn
            icon
            @click="showEditForm = true"
            >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
        </th>
        <th width="25%" rowspan="4">{{ $t('DetailedFlowchart.activities') }}</th>
        <th width="10%">{{ $t('DetailedFlowchart.study_epoch') }}</th>
        <template v-if="groupedVisits.length">
          <th v-for="(sv, index) in groupedVisits" :key="`epoch-${index}`" class="text-vertical">
            {{ getEpochName(sv, index) }}
          </th>
        </template>
        <template v-else>
          <th colspan="2"></th>
        </template>
      </tr>
      <tr>
        <th :style="`top: ${firstHeaderHeight}px`">{{ $t('DetailedFlowchart.visit_short_name') }}</th>
        <template v-if="groupedVisits.length">
          <th v-for="(sv, index) in groupedVisits" :key="`shortName-${index}`" :style="`top: ${firstHeaderHeight}px`">
            {{ sv.visitShortName }}
          </th>
        </template>
        <template v-else>
          <th colspan="2" :style="`top: ${firstHeaderHeight}px`"></th>
        </template>
      </tr>
      <tr>
        <th :style="`top: ${thirdHeaderRowTop}px`">{{ $t('DetailedFlowchart.study_week') }}</th>
        <template v-if="groupedVisits.length">
          <th v-for="(sv, index) in groupedVisits" :key="`week-${index}`" :style="`top: ${thirdHeaderRowTop}px`">
            {{ sv.studyWeekNumber }}
          </th>
        </template>
        <template v-else>
          <th colspan="2" :style="`top: ${thirdHeaderRowTop}px`"></th>
        </template>
      </tr>
      <tr>
        <th :style="`top: ${fourthHeaderRowTop}px`">{{ $t('DetailedFlowchart.visit_window') }}</th>
        <template v-if="groupedVisits.length">
          <th v-for="(sv, index) in groupedVisits" :key="`window-${index}`" :style="`top: ${fourthHeaderRowTop}px`">
            <template v-if="sv.minVisitWindowValue !== sv.maxVisitWindowValue">
              {{ sv.minVisitWindowValue }}/+{{ sv.maxVisitWindowValue }}
            </template>
            <template v-else>
              &plusmn;{{ sv.maxVisitWindowValue }}
            </template>
          </th>
        </template>
        <template v-else>
          <th colspan="2" :style="`top: ${fourthHeaderRowTop}px`"></th>
        </template>
      </tr>
    </thead>
    <tbody>
      <template v-for="(groups, flowchartGroup, flGroupIndex) in sortedStudyActivities">
        <tr v-if="!hideFlowchartGroups" :key="flowchartGroup" class="flowchart text-uppercase">
          <td>
            <v-btn
              v-if="!readOnly"
              icon
              @click="toggleRowState(`flgroup-${flGroupIndex}`)"
              >
              <v-icon>{{ getDisplayButtonIcon(`flgroup-${flGroupIndex}`) }}</v-icon>
            </v-btn>
          </td>
          <td class="text-strong">{{ flowchartGroup }}</td>
          <td></td>
          <td :colspan="groupedVisits.length + 1"></td>
        </tr>
        <template v-for="(subgroups, group, groupIndex) in groups">
          <template v-if="rowsDisplayState[`flgroup-${flGroupIndex}`] || hideFlowchartGroups">
            <tr :key="`${flowchartGroup}-${group}`" class="group">
              <td>
                <v-btn
                  v-if="!readOnly"
                  icon
                  @click="toggleRowState(`group-${flGroupIndex}-${groupIndex}`)"
                  >
                  <v-icon>{{ getDisplayButtonIcon(`group-${flGroupIndex}-${groupIndex}`) }}</v-icon>
                </v-btn>
              </td>
              <td class="text-strong">{{ group }}</td>
              <td>
                <v-btn
                  v-if="!readOnly"
                  icon
                  @click="value => toggleActivityGroupFlowchartDisplay(flowchartGroup, group)"
                  :title="$t('DetailedFlowchart.toggle_group_display')"
                  >
                  <v-icon v-if="getGroupDisplayState(flowchartGroup, group)" color="success">mdi-eye-outline</v-icon>
                  <v-icon v-else>mdi-eye-off-outline</v-icon>
                </v-btn>
              </td>
              <td :colspan="groupedVisits.length + 1"></td>
            </tr>
            <template v-for="(studyActivities, subgroup, subgroupIndex) in subgroups">
              <template v-if="rowsDisplayState[`group-${flGroupIndex}-${groupIndex}`]">
                <tr :key="`${flowchartGroup}-${group}-${subgroup}`">
                  <td>
                    <v-btn
                      v-if="!readOnly"
                      icon
                      @click="toggleRowState(`subgroup-${flGroupIndex}-${groupIndex}-${subgroupIndex}`)"
                      >
                      <v-icon>{{ getDisplayButtonIcon(`subgroup-${flGroupIndex}-${groupIndex}-${subgroupIndex}`) }}</v-icon>
                    </v-btn>
                  </td>
                  <td class="subgroup">
                    <div class="d-flex align-center">
                      <v-checkbox
                        v-if="!readOnly"
                        @change="value => toggleSubgroupActivitiesSelection(flowchartGroup, group, subgroup, value)"
                        on-icon="mdi-checkbox-multiple-marked"
                        off-icon="mdi-checkbox-multiple-blank-outline"
                        hide-details
                        />
                      {{ subgroup }}
                    </div>
                  </td>
                  <td>
                    <v-btn
                      v-if="!readOnly"
                      icon
                      @click="value => toggleActivitySubgroupFlowchartDisplay(flowchartGroup, group, subgroup)"
                      :title="$t('DetailedFlowchart.toggle_subgroup_display')"
                      >
                      <v-icon v-if="getSubgroupDisplayState(flowchartGroup, group, subgroup)" color="success">mdi-eye-outline</v-icon>
                      <v-icon v-else>mdi-eye-off-outline</v-icon>
                    </v-btn>
                  </td>
                  <td :colspan="groupedVisits.length + 1"></td>
                </tr>
                <template v-if="rowsDisplayState[`subgroup-${flGroupIndex}-${groupIndex}-${subgroupIndex}`]">
                  <tr v-for="studyActivity in studyActivities" :key="studyActivity.studyActivityUid">
                    <td></td>
                    <td class="activity">
                      <div class="d-flex align-center">
                        <v-checkbox
                          v-if="!readOnly"
                          hide-details
                          @change="value => toggleActivitySelection(studyActivity, value)"
                          :value="studyActivitySelection.findIndex(item => item.studyActivityUid === studyActivity.studyActivityUid) !== -1"
                          />
                        {{ studyActivity.activity.name }}
                      </div>
                    </td>
                    <td>
                      <v-btn
                        v-if="!readOnly"
                        icon
                        @click="toggleActivityFlowchartDisplay(studyActivity, !studyActivity.showActivityInProtocolFlowchart)"
                        :title="$t('DetailedFlowchart.toggle_activity_display')"
                        >
                        <v-icon v-if="studyActivity.showActivityInProtocolFlowchart" color="success">mdi-eye-outline</v-icon>
                        <v-icon v-else>mdi-eye-off-outline</v-icon>
                      </v-btn>
                    </td>
                    <td v-for="visit in groupedVisits" :key="`${studyActivity.studyActivityUid}-${visit.uid}`">
                      <v-checkbox
                        v-if="!readOnly && currentSelectionMatrix[studyActivity.studyActivityUid][visit.uid]"
                        v-model="currentSelectionMatrix[studyActivity.studyActivityUid][visit.uid].value"
                        color="success"
                        @change="value => updateSchedule(value, studyActivity.studyActivityUid, visit)"
                        :disabled="isCheckboxDisabled(studyActivity.studyActivityUid, visit.uid)"
                        hide-details
                        on-icon="mdi-checkbox-marked-circle-outline"
                        off-icon="mdi-checkbox-blank-circle-outline"
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
  </div>
  <study-activity-schedule-batch-edit-form
    :open="showBatchEditForm"
    :selection="studyActivitySelection"
    :current-selection-matrix="currentSelectionMatrix"
    @updated="getStudyActivitySchedules"
    @close="showBatchEditForm = false"
    />
  <v-dialog
    v-model="showEditForm"
    persistent
    max-width="600px"
    >
    <v-card color="dfltBackground">
      <v-card-title>
        <span class="dialog-title">{{ $t('DetailedFlowchart.edit_dialog_title') }}</span>
      </v-card-title>
      <v-card-text class="mt-4">
        <div class="white pa-4">
          <validation-observer ref="redirectObserver">
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-radio-group
                v-model="editTarget"
                :error-messages="errors"
                >
                <v-radio
                  :label="$t('DetailedFlowchart.study_activities')"
                  value="activities"
                  />
                <v-radio
                  :label="$t('DetailedFlowchart.study_epochs')"
                  value="epochs"
                  />
                <v-radio
                  :label="$t('DetailedFlowchart.study_visits')"
                  value="visits"
                  />
              </v-radio-group>
            </validation-provider>
          </validation-observer>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          class="secondary-btn"
          color="white"
          @click="showEditForm = false"
          >
          {{ $t('_global.cancel') }}
        </v-btn>
        <v-btn
          color="secondary"
          @click="redirectTo"
          >
          {{ $t('_global.confirm') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</div>
</template>

<script>
import { bus } from '@/main'
import { mapGetters } from 'vuex'
import study from '@/api/study'
import StudyActivityScheduleBatchEditForm from './StudyActivityScheduleBatchEditForm'
import studyEpochs from '@/api/studyEpochs'
import terms from '@/api/controlledTerminology/terms'

export default {
  components: {
    StudyActivityScheduleBatchEditForm
  },
  props: {
    readOnly: {
      type: Boolean,
      default: false
    },
    update: Number
  },
  computed: {
    ...mapGetters({
      studyActivities: 'studyActivities/studyActivities',
      sortedStudyActivities: 'studyActivities/sortedStudyActivities',
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    thirdHeaderRowTop () {
      return this.initialFirstHeaderHeight + this.firstHeaderHeight
    },
    fourthHeaderRowTop () {
      return this.firstHeaderHeight + (this.initialFirstHeaderHeight * 2)
    },
    groupedVisits () {
      const result = []
      let currentGroup = null
      let firstVisit = null
      let previousVisit = null

      function createFakeVisit () {
        const fakeVisit = {
          visitShortName: `${firstVisit.visitShortName}-${previousVisit.visitShortName}`,
          epochUid: firstVisit.epochUid,
          studyWeekNumber: `${firstVisit.studyWeekNumber}-${previousVisit.studyWeekNumber}`,
          minVisitWindowValue: firstVisit.minVisitWindowValue,
          maxVisitWindowValue: firstVisit.maxVisitWindowValue,
          consecutiveVisitGroup: firstVisit.consecutiveVisitGroup,
          uid: firstVisit.consecutiveVisitGroup,
          isGroup: true
        }
        result.push(fakeVisit)
      }

      for (const visit of this.studyVisits) {
        if (visit.consecutiveVisitGroup) {
          if (visit.consecutiveVisitGroup !== currentGroup) {
            if (currentGroup) {
              createFakeVisit()
            }
            firstVisit = visit
            currentGroup = visit.consecutiveVisitGroup
          }
        } else {
          currentGroup = null
          result.push(visit)
        }
        previousVisit = visit
      }
      if (currentGroup) {
        createFakeVisit()
      }
      return result
    }
  },
  data () {
    return {
      currentSelectionMatrix: {},
      editTarget: null,
      expandAllRows: false,
      hideFlowchartGroups: false,
      rowsDisplayState: {},
      epochs: [],
      initialFirstHeaderHeight: 0,
      firstHeaderHeight: 0,
      showBatchEditForm: false,
      showEditForm: false,
      studyActivitySchedules: [],
      studyActivitySelection: [],
      studyVisits: [],
      tableHeight: 500
    }
  },
  methods: {
    getEpochName (studyVisit, index) {
      if (this.epochs.length) {
        if (index === 0 || this.studyVisits[index].epochUid !== this.studyVisits[index - 1].epochUid) {
          const epoch = this.epochs.find(item => item.termUid === studyVisit.epochUid)
          return epoch.sponsorPreferredName
        }
      }
      return ''
    },
    isCheckboxDisabled (studyActivityUid, studyVisitUid) {
      const state = this.currentSelectionMatrix[studyActivityUid][studyVisitUid]
      return this.readOnly || (state.value && !state.uid) || (!state.value && state.uid !== null)
    },
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
    getGroupDisplayState (flgroup, group) {
      for (const items of Object.values(this.sortedStudyActivities[flgroup][group])) {
        for (const item of items) {
          if (item.showActivityGroupInProtocolFlowchart) {
            return true
          }
        }
      }
      return false
    },
    getSubgroupDisplayState (flgroup, group, subgroup) {
      for (const item of this.sortedStudyActivities[flgroup][group][subgroup]) {
        if (item.showActivitySubGroupInProtocolFlowchart) {
          return true
        }
      }
      return false
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
        this.studyActivitySelection.push(studyActivity)
      } else {
        for (let i = 0; i < this.studyActivitySelection.length; i++) {
          if (this.studyActivitySelection[i].studyActivityUid === studyActivity.studyActivityUid) {
            this.studyActivitySelection.splice(i, 1)
            break
          }
        }
      }
    },
    updateStudyActivity (studyActivity, data) {
      study.updateStudyActivity(this.selectedStudy.uid, studyActivity.studyActivityUid, data).then(resp => {
        const fgroup = studyActivity.flowchartGroup.sponsorPreferredName
        const group = (studyActivity.activity.activityGroup)
          ? studyActivity.activity.activityGroup.name : ''
        const subgroup = (studyActivity.activity.activitySubGroup)
          ? studyActivity.activity.activitySubGroup.name : ''
        this.sortedStudyActivities[fgroup][group][subgroup].filter((item, index) => {
          this.$store.commit('studyActivities/UPDATE_STUDY_ACTIVITY', resp.data)
        })
      })
    },
    /*
    ** Toggle group display in protocol flowchart.
    ** We need to store this information on each study activity...
    */
    toggleActivityGroupFlowchartDisplay (flgroup, group) {
      for (const items of Object.values(this.sortedStudyActivities[flgroup][group])) {
        if (items.length) {
          items.forEach(studyActivity => {
            const data = {
              showActivityGroupInProtocolFlowchart: !studyActivity.showActivityGroupInProtocolFlowchart
            }
            this.updateStudyActivity(studyActivity, data)
          })
        }
      }
    },
    /*
    ** Toggle subgroup display in protocol flowchart.
    ** We need to store this information on each study activity...
    */
    toggleActivitySubgroupFlowchartDisplay (flgroup, group, subgroup) {
      this.sortedStudyActivities[flgroup][group][subgroup].forEach(studyActivity => {
        const data = {
          showActivitySubGroupInProtocolFlowchart: !studyActivity.showActivitySubGroupInProtocolFlowchart
        }
        this.updateStudyActivity(studyActivity, data)
      })
    },
    toggleActivityFlowchartDisplay (studyActivity) {
      const data = {
        showActivityInProtocolFlowchart: !studyActivity.showActivityInProtocolFlowchart
      }
      this.updateStudyActivity(studyActivity, data)
    },
    updateGroupedSchedule (value, studyActivityUid, studyVisit) {
      if (value) {
        const data = []
        for (const iterator of this.studyVisits) {
          if (iterator.consecutiveVisitGroup === studyVisit.consecutiveVisitGroup) {
            data.push({
              method: 'POST',
              content: {
                studyActivityUid,
                studyVisitUid: iterator.uid
              }
            })
          }
        }
        study.studyActivityScheduleBatchOperations(this.selectedStudy.uid, data).then(resp => {
          const scheduleUids = resp.data.map(item => item.content.studyActivityScheduleUid)
          this.currentSelectionMatrix[studyActivityUid][studyVisit.uid].uid = scheduleUids
        })
      } else {
        const data = []
        for (const scheduleUid of this.currentSelectionMatrix[studyActivityUid][studyVisit.uid].uid) {
          data.push({
            method: 'DELETE',
            content: {
              uid: scheduleUid
            }
          })
        }
        study.studyActivityScheduleBatchOperations(this.selectedStudy.uid, data).then(resp => {
          this.currentSelectionMatrix[studyActivityUid][studyVisit.uid].uid = null
        })
      }
    },
    updateSchedule (value, studyActivityUid, studyVisit) {
      if (studyVisit.isGroup) {
        this.updateGroupedSchedule(value, studyActivityUid, studyVisit)
        return
      }
      if (value) {
        const data = {
          studyActivityUid,
          studyVisitUid: studyVisit.uid
        }
        study.createStudyActivitySchedule(this.selectedStudy.uid, data).then(resp => {
          this.currentSelectionMatrix[studyActivityUid][studyVisit.uid].uid = resp.data.studyActivityScheduleUid
        })
      } else {
        const scheduleUid = this.currentSelectionMatrix[studyActivityUid][studyVisit.uid].uid
        study.deleteStudyActivitySchedule(this.selectedStudy.uid, scheduleUid).then(resp => {
          this.currentSelectionMatrix[studyActivityUid][studyVisit.uid].uid = null
        })
      }
    },
    openBatchEditForm () {
      if (!this.studyActivitySelection.length) {
        bus.$emit('notification', { type: 'warning', msg: this.$t('DetailedFlowchart.batch_edit_no_selection') })
        return
      }
      this.showBatchEditForm = true
    },
    toggleActivitySelectionDisplay (value) {
      if (!this.studyActivitySelection.length) {
        bus.$emit('notification', { type: 'warning', msg: this.$t('DetailedFlowchart.batch_edit_no_selection') })
        return
      }
      const data = []
      for (const item of this.studyActivitySelection) {
        data.push({
          method: 'PATCH',
          content: {
            studyActivityUid: item.studyActivityUid,
            content: {
              showActivityInProtocolFlowchart: value
            }
          }
        })
      }
      study.studyActivityBatchOperations(this.selectedStudy.uid, data).then(resp => {
        bus.$emit('notification', {
          type: 'success',
          msg: this.$t('DetailedFlowchart.update_success')
        })
        this.studyActivitySelection.forEach(item => {
          this.$set(item, 'showActivityInProtocolFlowchart', value)
        })
      })
    },
    toggleSubgroupActivitiesSelection (flgroup, group, subgroup, value) {
      if (value) {
        this.studyActivitySelection = this.studyActivitySelection.concat(this.sortedStudyActivities[flgroup][group][subgroup])
      } else {
        for (const studyActivity of this.sortedStudyActivities[flgroup][group][subgroup]) {
          const index = this.studyActivitySelection.findIndex(item => item.studyActivityUid === studyActivity.studyActivityUid)
          this.studyActivitySelection.splice(index, 1)
        }
      }
    },
    getStudyActivitySchedules () {
      study.getStudyActivitySchedules(this.selectedStudy.uid).then(resp => {
        this.groupedVisits.forEach(visit => {
          Object.keys(this.currentSelectionMatrix).forEach(studyActivity => {
            this.$set(this.currentSelectionMatrix[studyActivity], visit.uid, { value: false, uid: null })
          })
        })
        resp.data.forEach(schedule => {
          const visit = this.studyVisits.find(item => item.uid === schedule.studyVisitUid)
          if (!visit.consecutiveVisitGroup) {
            this.$set(
              this.currentSelectionMatrix[schedule.studyActivityUid],
              visit.uid,
              { value: true, uid: schedule.studyActivityScheduleUid }
            )
          } else {
            const visitUid = visit.consecutiveVisitGroup
            if (!this.currentSelectionMatrix[schedule.studyActivityUid][visitUid].uid) {
              this.$set(
                this.currentSelectionMatrix[schedule.studyActivityUid],
                visitUid,
                { value: true, uid: [schedule.studyActivityScheduleUid] }
              )
            } else {
              this.currentSelectionMatrix[schedule.studyActivityUid][visitUid].uid.push(
                schedule.studyActivityScheduleUid
              )
            }
          }
        })
      })
    },
    async redirectTo () {
      const valid = await this.$refs.redirectObserver.validate()
      if (!valid) {
        return
      }
      this.showEditForm = false
      if (this.editTarget === 'activities') {
        this.$router.push({ name: 'StudyActivities', params: { tab: 'list' } })
      } else if (this.editTarget === 'epochs') {
        this.$router.push({ name: 'StudyDesign', params: { tab: 'epochs' } })
      } else {
        this.$router.push({ name: 'StudyDesign', params: { tab: 'visits' } })
      }
    },
    loadActivities () {
      this.$store.dispatch('studyActivities/fetchStudyActivities', { studyUid: this.selectedStudy.uid }).then(() => {
        for (const studyActivity of this.studyActivities) {
          this.$set(this.currentSelectionMatrix, studyActivity.studyActivityUid, {})
        }
        studyEpochs.getStudyVisits(this.selectedStudy.uid).then(resp => {
          this.studyVisits = resp.data.items
          this.getStudyActivitySchedules()
        })
      })
    },
    onResize () {
      this.tableHeight = window.innerHeight - this.$refs.tableContainer.getBoundingClientRect().y - 60
    }
  },
  mounted () {
    terms.getByCodelist('epochs').then(resp => {
      this.epochs = resp.data.items
    })
    this.loadActivities()
    this.onResize()
  },
  watch: {
    update () {
      this.loadActivities()
    }
  },
  updated () {
    this.firstHeaderHeight = this.$refs.firstHeader.clientHeight
    if (!this.initialFirstHeaderHeight) {
      this.initialFirstHeaderHeight = this.firstHeaderHeight
    }
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
  vertical-align: bottom;
  background-color: var(--v-greyBackground-base);
}
th, td {
  padding: 6px;
  font-size: 14px !important;
}
.sticky-header {
  overflow-y: auto;

  thead th {
    position: sticky;
    top: 0;
    z-index: 3;
  }
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
