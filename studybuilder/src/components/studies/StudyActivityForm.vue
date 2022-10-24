<template>
<div>
  <horizontal-stepper-form
    ref="stepper"
    :title="$t('StudyActivityForm.add_title')"
    :steps="steps"
    @close="cancel"
    @save="submit"
    :form-observer-getter="getObserver"
    :help-text="$t('_help.StudyActivityTable.general')"
    >
    <template v-slot:step.creationMode>
      <v-radio-group
        v-model="creationMode"
        >
        <v-radio :label="$t('StudyActivityForm.select_from_studies')" value="selectFromStudies" />
        <v-radio :label="$t('StudyActivityForm.select_from_library')" value="selectFromLibrary" />
        <v-radio :label="$t('StudyActivityForm.create_placeholder')" value="createPlaceholder" />
      </v-radio-group>
    </template>
    <template v-slot:step.selectStudies="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-select
            v-model="selectedStudies"
            :label="$t('StudySelectionTable.studies')"
            :items="studies"
            :error-messages="errors"
            item-text="studyId"
            clearable
            multiple
            return-object
            />
        </validation-provider>
      </validation-observer>
    </template>
    <template v-slot:step.selectFlowchartGroup="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-row>
            <v-col cols="4">
              <v-autocomplete
                v-model="currentFlowchartGroup"
                :label="$t('StudyActivityForm.flowchart_group')"
                :items="flowchartGroups"
                item-text="sponsorPreferredName"
                return-object
                :error-messages="errors"
                :hint="$t('_help.StudyActivityForm.flowchart_group')"
                persistent-hint
                clearable
                />
            </v-col>
          </v-row>
        </validation-provider>
      </validation-observer>
    </template>
    <template v-slot:step.selectFromStudies>
      <v-data-table
        key="fromStudiesSelection"
        :headers="selectionHeaders"
        :items="selectedActivities"
        >
        <template v-slot:item.name="{ item }">
          {{ item.activity.name }}
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn
            icon
            color="red"
            @click="unselectActivity(item)"
            >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </template>
    <template v-slot:step.selectFromStudies.after>
      <div class="mt-4 mx-4 text-subtitle-1 grey--text font-italic">
        {{ $t('StudyActivityForm.copy_activity_instructions') }}
      </div>
      <v-col cols="12">
        <study-selection-table
          ref="selectionTable"
          key="selectFromStudiesTable"
          :headers="studyActivityHeaders"
          data-fetcher-name="getAllStudyActivities"
          :extra-data-fetcher-filters="extraDataFetcherFilters"
          :studies="selectedStudies"
          :column-data-resource="`study/${selectedStudy.uid}/study-activities`"
          show-filter-bar-by-default
          >
          <template v-slot:header.actions>
            <div class="row">
              <v-btn
                icon
                color="primary"
                @click="selectAllStudyActivities()"
                :title="$t('StudyActivityForm.copy_all_activities')">
                <v-icon>mdi-content-copy</v-icon>
              </v-btn>
            </div>
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              icon
              :color="getCopyButtonColor(item)"
              :disabled="isStudyActivitySelected(item)"
              @click="selectStudyActivity(item)"
              :title="$t('StudyActivityForm.copy_activity')">
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
          </template>
        </study-selection-table>
      </v-col>
    </template>
    <template v-slot:step.selectFromLibrary>
      <v-data-table
        key="fromLibrarySelection"
        :headers="selectionHeaders"
        :items="selectedActivities"
        >
        <template v-slot:item.actions="{ item }">
          <v-btn
            icon
            color="red"
            @click="unselectActivity(item)"
            >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </template>
    <template v-slot:step.selectFromLibrary.after>
      <div class="mt-4 mx-4 text-subtitle-1 grey--text font-italic">
        {{ $t('StudyActivityForm.copy_activity_instructions') }}
      </div>
      <v-col cols="12">
        <n-n-table
          key="activityTable"
          :headers="activityHeaders"
          :items="activities"
          hide-default-switches
          hide-actions-menu
          show-filter-bar-by-default
          :items-per-page="15"
          elevation="0"
          :options.sync="options"
          :server-items-length="activitiesTotal"
          has-api
          @filter="getActivities"
          column-data-resource="concepts/activities/activities"
          :filters-modify-function="modifyFilters"
          >
          <template v-slot:item.actions="{ item }">
            <v-btn
              icon
              :color="getCopyButtonColor(item)"
              :disabled="isActivitySelected(item)"
              @click="selectActivity(item)"
              :title="$t('StudyActivityForm.copy_activity')">
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
          </template>
          <template v-slot:header.actions>
            <div class="row">
              <v-btn
                icon
                color="primary"
                @click="selectAllActivities()"
                :title="$t('StudyActivityForm.copy_all_activities')">
                <v-icon>mdi-content-copy</v-icon>
              </v-btn>
            </div>
          </template>
        </n-n-table>
      </v-col>
    </template>
  </horizontal-stepper-form>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import activities from '@/api/activities'
import statuses from '@/constants/statuses'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import NNTable from '@/components/tools/NNTable'
import StudySelectionTable from '@/components/studies/StudySelectionTable'
import _isEmpty from 'lodash/isEmpty'
import _isEqual from 'lodash/isEqual'

export default {
  components: {
    ConfirmDialog,
    HorizontalStepperForm,
    NNTable,
    StudySelectionTable
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyActivities: 'studyActivities/studyActivities'
    })
  },
  data () {
    return {
      creationMode: 'selectFromLibrary',
      activities: [],
      extraDataFetcherFilters: {
        'activity.status': { v: [statuses.FINAL] }
      },
      options: {},
      activitiesTotal: 0,
      activityHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyActivity.activity_group'), value: 'activityGroup.name', externalFilterSource: 'concepts/activities/activity-groups$name' },
        { text: this.$t('StudyActivity.activity_sub_group'), value: 'activitySubGroup.name', externalFilterSource: 'concepts/activities/activity-sub-groups$name' },
        { text: this.$t('StudyActivity.activity'), value: 'name', externalFilterSource: 'concepts/activities/activities$name' }
      ],
      currentFlowchartGroup: null,
      flowchartGroups: [],
      selectedStudies: [],
      steps: [],
      studies: [],
      selectFromStudiesSteps: [
        { name: 'creationMode', title: this.$t('StudyActivityForm.creation_mode_title') },
        { name: 'selectStudies', title: this.$t('StudyActivityForm.select_studies') },
        { name: 'selectFromStudies', title: this.$t('StudyActivityForm.select_from_studies_title') }
      ],
      selectFromLibrarySteps: [
        { name: 'creationMode', title: this.$t('StudyActivityForm.creation_mode_title') },
        { name: 'selectFlowchartGroup', title: this.$t('StudyActivityForm.flowchart_group_title') },
        { name: 'selectFromLibrary', title: this.$t('StudyActivityForm.select_from_library_title') }
      ],
      createPlaceholderSteps: [
        { name: 'creationMode', title: this.$t('StudyActivityForm.creation_mode_title') },
        { name: 'selectFlowchartGroup', title: this.$t('StudyActivityForm.flowchart_group_title') }
      ],
      selectionHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyActivityForm.flowchart_group'), value: 'flowchartGroup.sponsorPreferredName' },
        { text: this.$t('StudyActivity.activity_group'), value: 'activity.activityGroup.name' },
        { text: this.$t('StudyActivity.activity_sub_group'), value: 'activity.activitySubGroup.name' },
        { text: this.$t('StudyActivity.activity'), value: 'name' }
      ],
      selectedActivities: [],
      studyActivityHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyActivityForm.study_id'), value: 'studyUid' },
        { text: this.$t('StudyActivityForm.flowchart_group'), value: 'flowchartGroup.sponsorPreferredName' },
        { text: this.$t('StudyActivity.activity_group'), value: 'activity.activityGroup.name' },
        { text: this.$t('StudyActivity.activity_sub_group'), value: 'activity.activitySubGroup.name' },
        { text: this.$t('StudyActivity.activity'), value: 'activity.name' }
      ],
      filters: ''
    }
  },
  methods: {
    async cancel () {
      if (!_isEmpty(this.selectedActivities)) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue')
        }
        if (await this.$refs.confirm.open(this.$t('_global.cancel_changes'), options)) {
          this.close()
        }
      } else {
        this.close()
      }
    },
    close () {
      this.$emit('close')
      this.selectedActivities = []
      this.currentFlowchartGroup = null
      this.creationMode = 'selectFromLibrary'
      this.steps = this.selectFromLibrarySteps
      this.selectedStudies = []
      this.$refs.stepper.reset()
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    initFromStudyActivity (studyActivity) {
      this.steps = this.editSteps
      this.form = JSON.parse(JSON.stringify(studyActivity))
    },
    getActivities (filters, sort) {
      if (filters !== undefined && !_isEqual(filters, this.filters)) {
        // New filters, also reset current page
        this.filters = filters
        this.options.page = 1
      }
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      if (this.filters && this.filters !== undefined) {
        const filtersObj = JSON.parse(this.filters)
        if (filtersObj.activityGroup) {
          params.activityGroupNames = []
          filtersObj.activityGroup.v.forEach(value => {
            params.activityGroupNames.push(value)
          })
          delete filtersObj.activityGroup
        }
        if (filtersObj.activitySubGroup) {
          params.activitySubGroupNames = []
          filtersObj.activitySubGroup.v.forEach(value => {
            params.activitySubGroupNames.push(value)
          })
          delete filtersObj.activitySubGroup
        }
        if (filtersObj.name) {
          params.activityNames = []
          filtersObj.name.v.forEach(value => {
            params.activityNames.push(value)
          })
          delete filtersObj.name
        }
        if (Object.keys(filtersObj).length !== 0 && filtersObj.constructor === Object) {
          params.filters = JSON.stringify(filtersObj)
        }
      }
      if (this.options.sortBy && this.options.sortBy.length !== 0 && sort !== undefined) {
        params.sortBy = `{"${this.options.sortBy[0]}":${!sort}}`
      }
      activities.get(params, 'activities').then(resp => {
        this.activities = resp.data.items
        this.activitiesTotal = resp.data.total
      })
    },
    modifyFilters (jsonFilter, params) {
      if (jsonFilter.activityGroup) {
        params.activityGroupNames = []
        jsonFilter.activityGroup.v.forEach(value => {
          params.activityGroupNames.push(value)
        })
        delete jsonFilter.activityGroup
      }
      if (jsonFilter.activitySubGroup) {
        params.activitySubGroupNames = []
        jsonFilter.activitySubGroup.v.forEach(value => {
          params.activitySubGroupNames.push(value)
        })
        delete jsonFilter.activitySubGroup
      }
      if (jsonFilter.name) {
        params.activityNames = []
        jsonFilter.name.v.forEach(value => {
          params.activityNames.push(value)
        })
        delete jsonFilter.name
      }
      const filters = {
        jsonFilter: jsonFilter,
        params: params
      }
      return filters
    },
    selectActivity (activity) {
      if (!this.currentFlowchartGroup) {
        return
      }
      const activityCopy = { ...activity }
      activityCopy.flowchartGroup = { ...this.currentFlowchartGroup }
      this.selectedActivities.push(activityCopy)
    },
    selectAllActivities () {
      if (!this.currentFlowchartGroup) {
        return
      }
      for (const activity of this.activities) {
        if (!this.selectedActivities.find(item => item.uid === activity.uid)) {
          const activityCopy = { ...activity }
          activityCopy.flowchartGroup = { ...this.currentFlowchartGroup }
          this.selectedActivities.push(activityCopy)
        }
      }
    },
    selectStudyActivity (studyActivity) {
      const copy = { ...studyActivity }
      this.selectedActivities.push(copy)
    },
    selectAllStudyActivities () {
      for (const studyActivity of this.$refs.selectionTable.studySelectionItems) {
        if (!this.isStudyActivitySelected(studyActivity)) {
          const copy = { ...studyActivity }
          this.selectedActivities.push(copy)
        }
      }
    },
    unselectActivity (activity) {
      this.selectedActivities = this.selectedActivities.filter(item => item.uid !== activity.uid)
    },
    getCopyButtonColor (activity) {
      const selected = this.selectedActivities.find(item => item.uid === activity.uid)
      return (!selected) ? 'primary' : ''
    },
    isActivitySelected (activity) {
      if (this.studyActivities) {
        let selected = this.selectedActivities.find(item => item.uid === activity.uid)
        if (!selected && this.studyActivities.length) {
          selected = this.studyActivities.find(item => item.activity.uid === activity.uid)
        }
        return !this.currentFlowchartGroup || selected !== undefined
      }
      return false
    },
    isStudyActivitySelected (studyActivity) {
      let selected = this.selectedActivities.find(item => item.activity.uid === studyActivity.activity.uid)
      if (!selected && this.studyActivities.length) {
        selected = this.studyActivities.find(item => item.activity.uid === studyActivity.activity.uid)
      }
      return selected !== undefined
    },
    async submit () {
      if (this.creationMode !== 'selectFromLibrary' && this.creationMode !== 'selectFromStudies') {
        return
      }
      if (!this.selectedActivities.length) {
        return
      }
      for (let cpt = 0; cpt < this.selectedActivities.length; cpt++) {
        const item = this.selectedActivities[cpt]
        let payload
        if (this.creationMode === 'selectFromLibrary') {
          payload = {
            flowchartGroupUid: item.flowchartGroup.termUid,
            activityUid: item.uid
          }
        } else {
          payload = {
            flowchartGroupUid: item.flowchartGroup.termUid,
            activityUid: item.activity.uid
          }
        }
        await study.createStudyActivity(this.selectedStudy.uid, payload)
      }
      bus.$emit('notification', { type: 'success', msg: this.$t('StudyActivityForm.add_success') })
      this.$emit('added')
      this.close()
    }
  },
  created () {
    this.steps = this.selectFromLibrarySteps
  },
  mounted () {
    terms.getByCodelist('flowchartGroups').then(resp => {
      this.flowchartGroups = resp.data.items
    })
    study.get({ hasStudyActivity: true }).then(resp => {
      this.studies = resp.data.items.filter(study => study.uid !== this.selectedStudy.uid)
    })
  },
  watch: {
    studyEndpoint (val) {
      if (val) {
        this.initFromStudyEndpoint(val)
      } else {
        this.form = this.getInitialForm()
      }
    },
    creationMode (value) {
      if (value === 'selectFromStudies') {
        this.steps = this.selectFromStudiesSteps
      } else if (value === 'selectFromLibrary') {
        this.steps = this.selectFromLibrarySteps
      } else {
        this.steps = this.createPlaceholderSteps
      }
    }
  }
}
</script>

<style scoped lang="scss">
.v-stepper {
  background-color: var(--v-dfltBackground-base) !important;
  box-shadow: none;
}

.step-title {
  color: var(--v-secondary-base) !important;
}
</style>
