<template>
<div>
  <horizontal-stepper-form
    ref="stepper"
    :title="$t('StudyActivityInstructionBatchForm.add_title')"
    :steps="steps"
    @close="close"
    @save="submit"
    :form-observer-getter="getObserver"
    :help-text="$t('_help.StudyActivityInstructionBatchForm.general')"
    @stepLoaded="onStepLoaded"
    :extra-step-validation="extraStepValidation"
    >
    <template v-slot:step.creationMode>
      <v-radio-group
        data-cy="objective-method-radio"
        v-model="creationMode"
        >
        <v-radio :label="$t('StudyActivityInstructionBatchForm.select_mode')" value="select" />
        <v-radio :label="$t('StudyActivityInstructionBatchForm.template_mode')" value="template" />
        <v-radio :label="$t('StudyActivityInstructionBatchForm.scratch_mode')" value="scratch" />
      </v-radio-group>
    </template>
    <template v-slot:step.creationMode.after>
      <study-activity-selection-table
        class="ma-4"
        :selection="studyActivities"
        :title="$t('StudyActivityInstructionBatchForm.batch_table_title')"
        />
    </template>
    <template v-slot:step.selectStudies="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-select
            :data-cy="$t('StudySelectionTable.select_studies')"
            v-model="selectedStudies"
            :label="$t('StudySelectionTable.select_studies')"
            :items="studies"
            :error-messages="errors"
            item-text="studyId"
            clearable
            multiple
            class="pt-10"
            return-object
            />
        </validation-provider>
      </validation-observer>
    </template>
    <template v-slot:step.selectFromStudies>
      <p class="grey--text text-subtitle-1 font-weight-bold">{{ $t('StudyActivityInstructionBatchForm.selected_items') }}</p>
      <v-data-table
        data-cy="selected-instructions-table"
        :headers="selectedInstructionsHeaders"
        :items="selectedInstructions"
        >
        <template v-slot:item.activityInstructionName="{ item }">
          <n-n-parameter-highlighter
            :name="item.activityInstructionName"
            :show-prefix-and-postfix="false"
            />
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn
            icon
            color="red"
            @click="unselectInstruction(item)"
            >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </template>
    <template v-slot:step.selectFromStudies.after>
      <p class="grey--text text-subtitle-1 font-weight-bold mb-0 ml-3">{{ $t('StudyObjectiveForm.copy_instructions') }}</p>
      <v-col cols="12" flat class="pt-0 mt-0">
        <study-selection-table
          :headers="activityInstructionHeaders"
          data-fetcher-name="getAllStudyActivityInstructions"
          :extra-data-fetcher-filters="extraStudyActivityInstructionFilters"
          @item-selected="selectStudyActivityInstruction"
          :studies="selectedStudies"
          >
          <template v-slot:item.activityInstructionName="{ item }">
            <n-n-parameter-highlighter
              :name="item.activityInstructionName"
              :show-prefix-and-postfix="false"
              />
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              :data-cy="$t('StudySelectionTable.copy_item')"
              icon
              :color="getCopyButtonColor(item)"
              :disabled="isStudyActivityInstructionSelected(item)"
              @click="selectStudyActivityInstruction(item)"
              :title="$t('StudySelectionTable.copy_item')">
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
          </template>
        </study-selection-table>
      </v-col>
    </template>

    <template v-slot:step.selectTemplate>
      <p class="grey--text text-subtitle-1 font-weight-bold">{{ $t('StudyActivityInstructionBatchForm.select_template_title') }}</p>
        <v-card flat class="parameterBackground">
          <v-card-text>
            <n-n-parameter-highlighter :name="selectedTemplateName" default-color="orange"/>
          </v-card-text>
        </v-card>
    </template>
    <template v-slot:step.selectTemplate.after>
      <p class="grey--text text-subtitle-1 font-weight-bold mb-0 ml-3">{{ $t('StudyActivityInstructionBatchForm.copy_instructions') }}</p>
      <v-col cols="12" class="pt-0">
        <n-n-table
          ref="templateTable"
          key="templatesTable"
          :headers="tplHeaders"
          :items="templates"
          hide-default-switches
          hide-actions-menu
          :items-per-page="15"
          elevation="0"
          :options.sync="templatesOptions"
          :server-items-length="templatesTotal"
          show-filter-bar-by-default
          has-api
          column-data-resource="activity-description-templates"
          :initial-column-data="prefilteredTplHeaders"
          @filter="getTemplates"
          >
          <template v-slot:item.indications.name="{ item }">
            <template v-if="item.indications">
              {{ item.indications|names }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template v-slot:item.activityGroups.name="{ item }">
            <template v-if="item.activityGroups.length">
              {{ item.activityGroups[0].name }}
            </template>
          </template>
          <template v-slot:item.activitySubGroups.name="{ item }">
            <template v-if="item.activitySubGroups.length">
              {{ item.activitySubGroups[0].name }}
            </template>
          </template>
          <template v-slot:item.activities.name="{ item }">
            <template v-if="item.activities && item.activities.length">
              {{ item.activities[0].name }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template v-slot:item.name="{ item }">
            <n-n-parameter-highlighter :name="item.name" default-color="orange" />
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              :data-cy="$t('StudyActivityInstructionBatchForm.copy_template')"
              icon
              color="primary"
              @click="selectTemplate(item)"
              :title="$t('StudyActivityInstructionBatchForm.copy_template')">
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
          </template>
        </n-n-table>
      </v-col>
    </template>
    <template v-slot:step.createTemplate="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <n-n-template-input-field
            :data-cy="$t('StudyActivityInstructionBatchForm.name')"
            v-model="templateForm.name"
            :label="$t('StudyActivityInstructionBatchForm.name')"
            :items="parameterTypes"
            :error-messages="errors"
            show-drop-down-early
            />
          <div class="dialog-sub-title">{{ $t('_global.indexing') }}</div>
          <activity-template-indexing-form
            :form="templateForm"
            />
        </validation-provider>
      </validation-observer>
    </template>
    <template v-slot:step.createInstructionText="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <v-progress-circular
          v-if="loadingParameters"
          indeterminate
          color="secondary"
          />

        <template v-if="form.activityInstructionTemplate !== undefined">
          <parameter-value-selector
            ref="paramSelector"
            :value="parameters"
            :template="form.activityInstructionTemplate.name"
            color="white"
            />
        </template>
      </validation-observer>
    </template>
  </horizontal-stepper-form>
</div>
</template>

<script>
import activityDescriptionTemplates from '@/api/activityDescriptionTemplates'
import ActivityTemplateIndexingForm from '@/components/library/ActivityTemplateIndexingForm'
import { bus } from '@/main'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import instances from '@/utils/instances'
import libraryConstants from '@/constants/libraries'
import { mapGetters } from 'vuex'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector'
import filteringParameters from '@/utils/filteringParameters'
import statuses from '@/constants/statuses'
import study from '@/api/study'
import StudyActivitySelectionTable from './StudyActivitySelectionTable'
import StudySelectionTable from './StudySelectionTable'
import templateParameterTypes from '@/api/templateParameterTypes'

export default {
  components: {
    ActivityTemplateIndexingForm,
    HorizontalStepperForm,
    NNParameterHighlighter,
    NNTable,
    NNTemplateInputField,
    ParameterValueSelector,
    StudyActivitySelectionTable,
    StudySelectionTable
  },
  props: {
    studyActivities: Array,
    currentStudyActivityInstructions: Array
  },
  created () {
    this.steps = this.selectFromStudiesSteps
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    selectedTemplateName () {
      return (this.form.activityInstructionTemplate) ? this.form.activityInstructionTemplate.name : ''
    },
    selectedActivityGroups () {
      const result = []
      for (const studyActivity of this.studyActivities) {
        result.push(studyActivity.activity.activityGroup)
      }
      return result
    },
    selectedActivitySubGroups () {
      const result = []
      for (const studyActivity of this.studyActivities) {
        result.push(studyActivity.activity.activitySubGroup)
      }
      return result
    },
    prefilteredTplHeaders () {
      return {
        'activityGroups.name': this.selectedActivityGroups.map(item => item.name),
        'activitySubGroups.name': this.selectedActivitySubGroups.map(item => item.name)
      }
    }
  },
  data () {
    return {
      activityInstructionHeaders: [
        { text: this.$t('Study.study_id'), value: 'studyUid' },
        { text: this.$t('StudyActivityInstructionBatchForm.instruction_text'), value: 'activityInstructionName' },
        { text: this.$t('_global.actions'), value: 'actions', width: '5%' }
      ],
      creationMode: 'select',
      extraStudyActivityInstructionFilters: {

      },
      form: {},
      loadingParameters: false,
      parameters: [],
      parameterTypes: [],
      selectedInstructions: [],
      selectedInstructionsHeaders: [
        { text: this.$t('Study.study_id'), value: 'studyId' },
        { text: this.$t('StudyActivityInstructionBatchForm.instruction_text'), value: 'activityInstructionName' },
        { text: this.$t('_global.actions'), value: 'actions', width: '5%' }
      ],
      selectedStudies: [],
      selectFromStudiesSteps: [
        { name: 'creationMode', title: this.$t('StudyActivityInstructionBatchForm.creation_mode_title') },
        { name: 'selectStudies', title: this.$t('StudyActivityInstructionBatchForm.select_studies') },
        { name: 'selectFromStudies', title: this.$t('StudyActivityInstructionBatchForm.select_from_studies_title') }
      ],
      createFromTemplateSteps: [
        { name: 'creationMode', title: this.$t('StudyActivityInstructionBatchForm.creation_mode_title') },
        { name: 'selectTemplate', title: this.$t('StudyActivityInstructionBatchForm.select_tpl_title') },
        { name: 'createInstructionText', title: this.$t('StudyActivityInstructionBatchForm.create_text_title') }
      ],
      scratchModeSteps: [
        { name: 'creationMode', title: this.$t('StudyActivityInstructionBatchForm.creation_mode_title') },
        { name: 'createTemplate', title: this.$t('StudyActivityInstructionBatchForm.create_template_title') },
        { name: 'createInstructionText', title: this.$t('StudyActivityInstructionBatchForm.create_text_title') }
      ],
      steps: [],
      studies: [],
      templateForm: {},
      templates: [],
      templatesTotal: 0,
      templatesFilters: {},
      templatesOptions: {},
      tplHeaders: [
        { text: this.$t('_global.indications'), value: 'indications.name' },
        { text: this.$t('StudyActivity.activity_group'), value: 'activityGroups.name' },
        { text: this.$t('StudyActivity.activity_sub_group'), value: 'activitySubGroups.name' },
        { text: this.$t('StudyActivity.activity'), value: 'activities.name' },
        { text: this.$t('_global.template'), value: 'name', width: '30%' },
        { text: this.$t('_global.actions'), value: 'actions', width: '5%' }
      ]
    }
  },
  methods: {
    close () {
      this.creationMode = 'select'
      this.$refs.stepper.reset()
      this.$emit('close')
      this.templateForm = {}
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    async loadParameters (template) {
      if (template) {
        this.loadingParameters = true
        const resp = await activityDescriptionTemplates.getObjectTemplateParameters(template.uid)
        this.parameters = resp.data
        /* Filter received parameters based on current study activity selection */
        for (const parameterValues of this.parameters) {
          if (parameterValues.name === 'ActivityGroup') {
            const activityGroupUids = this.selectedActivityGroups.map(item => item.uid)
            parameterValues.values = parameterValues.values.filter(item => activityGroupUids.indexOf(item.uid) !== -1)
          } else if (parameterValues.name === 'ActivitySubGroup') {
            const activitySubGroupUids = this.selectedActivitySubGroups.map(item => item.uid)
            parameterValues.values = parameterValues.values.filter(item => activitySubGroupUids.indexOf(item.uid) !== -1)
          }
        }
        this.loadingParameters = false
      } else {
        this.parameters = []
      }
    },
    getTemplates (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.templatesOptions, filters, sort, filtersUpdated)
      params.status = statuses.FINAL
      const newFilters = (filters) ? JSON.parse(filters) : {}
      newFilters['activityGroups.uid'] = { v: this.selectedActivityGroups.map(item => item.uid) }
      newFilters['activitySubGroups.uid'] = { v: this.selectedActivitySubGroups.map(item => item.uid) }
      params.filters = JSON.stringify(newFilters)
      params.operator = 'or'
      activityDescriptionTemplates.get(params).then(resp => {
        // Apply filtering on library here because we cannot mix operators in API queries...
        this.templates = resp.data.items.filter(item => item.library.name === libraryConstants.LIBRARY_SPONSOR)
        this.templatesTotal = resp.data.total
      })
    },
    async selectTemplate (template) {
      await this.loadParameters(template)
      this.$set(this.form, 'activityInstructionTemplate', {})
      this.$set(this.form, 'activityInstructionTemplate', template)
    },
    selectStudyActivityInstruction (studyActivityInstruction) {
      this.selectedInstructions.push(studyActivityInstruction)
    },
    unselectStudyActivityInstruction (studyActivityInstruction) {
      this.selectedInstructions = this.selectedInstructions.filter(item => item.activyInstructionName !== studyActivityInstruction.activyInstructionName)
    },
    isStudyActivityInstructionSelected (studyActivityInstruction) {
      let selected = this.selectedInstructions.find(item => item.activityInstructionUid === studyActivityInstruction.activityInstructionUid)
      if (!selected && this.currentStudyActivityInstructions.length) {
        selected = this.currentStudyActivityInstructions.find(item => item.activyInstructionUid === studyActivityInstruction.activyInstructionUid)
      }
      return selected !== undefined
    },
    getCopyButtonColor (item) {
      return (!this.isStudyActivityInstructionSelected(item) ? 'primary' : '')
    },
    async extraStepValidation (step) {
      if (this.creationMode !== 'scratch' || step !== 2) {
        return true
      }
      if (this.form.activityInstructionTemplate && this.form.activityInstructionTemplate.name === this.templateForm.name) {
        return true
      }
      const data = { ...this.templateForm, studyUid: this.selectedStudy.uid }
      data.libraryName = libraryConstants.LIBRARY_USER_DEFINED
      if (data.indications) {
        data.indicationUids = data.indications.map(indication => indication.termUid)
        delete data.indications
      }
      if (data.activityGroup) {
        data.activityGroupUids = [data.activityGroup]
        delete data.activityGroup
      }
      if (data.activitySubGroups) {
        data.activitySubGroupUids = data.activitySubGroups
        delete data.activitySubGroups
      }
      if (data.activities) {
        data.activityUids = data.activities.map(activity => activity.uid)
        delete data.activities
      }
      try {
        const resp = await activityDescriptionTemplates.create(data)
        await activityDescriptionTemplates.approve(resp.data.uid)
        this.$set(this.form, 'activityInstructionTemplate', resp.data)
      } catch (error) {
        return false
      }
      this.loadParameters(this.form.activityInstructionTemplate)
      return true
    },
    async submit () {
      const operations = []
      if (this.creationMode === 'template' || this.creationMode === 'scratch') {
        for (const studyActivity of this.studyActivities) {
          operations.push({
            method: 'POST',
            content: {
              activityInstructionData: {
                activityInstructionTemplateUid: this.form.activityInstructionTemplate.uid,
                parameterValues: await instances.formatParameterValues(this.parameters),
                libraryName: this.form.activityInstructionTemplate.library.name
              },
              studyActivityUid: studyActivity.studyActivityUid
            }
          })
        }
      } else if (this.creationMode === 'select') {
        for (const studyActivity of this.studyActivities) {
          for (const studyActivityInstruction of this.selectedInstructions) {
            operations.push({
              method: 'POST',
              content: {
                activityInstructionUid: studyActivityInstruction.activityInstructionUid,
                studyActivityUid: studyActivity.studyActivityUid
              }
            })
          }
        }
      }
      if (operations.length === 0) {
        return
      }
      await study.studyActivityInstructionBatchOperations(this.selectedStudy.uid, operations)
      this.$emit('added')
      bus.$emit('notification', { msg: this.$t('StudyActivityInstructionBatchForm.add_success') })
      this.close()
    },
    onStepLoaded (step) {
      if (this.creationMode === 'template' && step === 2) {
        this.$refs.templateTable.loading = false
      }
    }
  },
  mounted () {
    this.getTemplates()
    study.get({ hasStudyActivityInstruction: true }).then(resp => {
      this.studies = resp.data.items.filter(study => study.uid !== this.selectedStudy.uid)
    })
    templateParameterTypes.getTypes().then(resp => {
      this.parameterTypes = resp.data
    })
  },
  watch: {
    creationMode (value) {
      if (value === 'template') {
        this.steps = this.createFromTemplateSteps
      } else if (value === 'select') {
        this.steps = this.selectFromStudiesSteps
      } else {
        this.steps = this.scratchModeSteps
      }
    }
  }
}
</script>
