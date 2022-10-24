<template>
<div>
  <horizontal-stepper-form
    ref="stepper"
    :title="title"
    :steps="steps"
    @close="close"
    @save="submit"
    :form-observer-getter="getObserver"
    :editable="studyObjective !== undefined && studyObjective !== null"
    :extra-step-validation="createTemplate"
    :helpItems="helpItems"
    :editData="form"
    >
    <template v-if="!studyObjective" v-slot:step.creationMode>
      <v-radio-group
        v-model="creationMode"
        >
        <v-radio data-cy="objective-from-select" :label="$t('StudyObjectiveForm.select_mode')" value="select" />
        <v-radio data-cy="objective-from-template" :label="$t('StudyObjectiveForm.template_mode')" value="template" />
        <v-radio data-cy="objective-from-scratch" :label="$t('StudyObjectiveForm.scratch_mode')" value="scratch" />
      </v-radio-group>
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
    <template v-slot:step.selectObjective>
      <p class="grey--text text-subtitle-1 font-weight-bold">{{ $t('StudyObjectiveForm.selected_objectives') }}</p>
      <v-data-table
        data-cy="selected-objectives-table"
        :headers="selectedObjectiveHeaders"
        :items="selectedStudyObjectives"
        >
        <template v-slot:item.actions="{ item }">
          <v-btn
            icon
            color="red"
            @click="unselectStudyObjective(item)"
            >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </template>
    <template v-slot:step.selectObjective.after>
      <p class="grey--text text-subtitle-1 font-weight-bold mb-0 ml-3">{{ $t('StudyObjectiveForm.copy_instructions') }}</p>
      <v-col cols="12" flat class="pt-0 mt-0">
        <study-selection-table
          :headers="objectiveHeaders"
          data-fetcher-name="getAllStudyObjectives"
          :extra-data-fetcher-filters="extraStudyObjectiveFilters"
          @item-selected="selectStudyObjective"
          :studies="selectedStudies"
          >
          <template v-slot:item.objective.name="{ item }">
            <n-n-parameter-highlighter :name="item.objective.name" />
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              :data-cy="$t('StudySelectionTable.copy_item')"
              icon
              :color="getCopyButtonColor(item)"
              :disabled="isStudyObjectiveSelected(item)"
              @click="selectStudyObjective(item)"
              :title="$t('StudySelectionTable.copy_item')">
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
          </template>
        </study-selection-table>
      </v-col>
    </template>
    <template v-slot:step.selectTemplate>
      <v-card flat class="parameterBackground">
        <v-card-text>
          <n-n-parameter-highlighter
            :name="selectedTemplateName"
            default-color="orange"
            :default-parameter-values="selectedDefaultParameterValues"
            />
        </v-card-text>
      </v-card>
    </template>
    <template v-slot:step.selectTemplate.after>
      <p class="grey--text text-subtitle-1 font-weight-bold mb-0 ml-3 mt-2">{{ $t('StudyObjectiveForm.copy_instructions') }}</p>
      <v-col cols="12" class="pt-0">
        <n-n-table
          key="templatesTable"
          :headers="tplHeaders"
          :items="expandedTemplates"
          hide-default-switches
          hide-actions-menu
          show-filter-bar-by-default
          :items-per-page="15"
          elevation="0"
          :options.sync="options"
          :server-items-length="total"
          has-api
          :column-data-resource="`objective-templates`"
          @filter="getObjectiveTemplates"
          >
          <template v-slot:item.categories="{ item }">
            <template v-if="item.defaultParameterValuesSet === undefined">
              <template v-if="item.categories">
                {{ item.categories|terms }}
              </template>
              <template v-else>
                {{ $t('_global.not_applicable_long') }}
              </template>
            </template>
          </template>
          <template v-slot:item.confirmatoryTesting="{ item }">
            <template v-if="item.defaultParameterValuesSet === undefined">
              <template v-if="item.confirmatoryTesting !== null">
                {{ item.confirmatoryTesting|yesno }}
              </template>
              <template v-else>
                {{ $t('_global.not_applicable_long') }}
              </template>
            </template>
          </template>
          <template v-slot:item.indications="{ item }">
            <template v-if="item.defaultParameterValuesSet === undefined">
              <template v-if="item.indications">
                {{ item.indications|names }}
              </template>
              <template v-else>
                {{ $t('_global.not_applicable_long') }}
              </template>
            </template>
          </template>
          <template v-slot:item.name="{ item }">
            <n-n-parameter-highlighter
              v-if="item.defaultParameterValuesSet === undefined"
              :name="item.name"
              default-color="orange"
              />
            <n-n-parameter-highlighter
              v-else
              :name="item.name"
              default-color="orange"
              :default-parameter-values="item.defaultParameterValues"
              />
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              :data-cy="$t('StudyObjectiveForm.copy_template')"
              icon
              color="primary"
              @click="selectObjectiveTemplate(item)"
              :title="$t('StudyObjectiveForm.copy_template')">
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
          </template>
        </n-n-table>
      </v-col>
    </template>
    <template v-slot:step.editObjective="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <v-progress-circular
          v-if="loadingParameters"
          indeterminate
          color="secondary"
          />

        <parameter-value-selector
          ref="paramSelector"
          v-model="parameters"
          :template="studyObjective ? studyObjective.objective.objectiveTemplate.name : form.objectiveTemplate.name"
          :preview-text="$t('ParameterValueSelector.preview')"
          color="white"
          />
      </validation-observer>
    </template>
    <template v-slot:step.createTemplate="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <n-n-template-input-field
            :data-cy="$t('ObjectiveTemplateForm.name')"
            v-model="templateForm.name"
            :label="$t('ObjectiveTemplateForm.name')"
            :items="parameterTypes"
            :error-messages="errors"
            :show-drop-down-early="true"
            />
        </validation-provider>
      </validation-observer>
    </template>
    <template v-slot:step.createObjective="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <v-progress-circular
          v-if="loadingParameters"
          indeterminate
          color="secondary"
          />

        <template v-if="form.objectiveTemplate !== undefined">
          <parameter-value-selector
            ref="paramSelector"
            :value="parameters"
            :template="form.objectiveTemplate.name"
            color="white"
            preview-text=" "
            />
        </template>
      </validation-observer>
    </template>

    <template v-slot:step.objectiveLevel>
      <v-row>
        <v-col cols="11">
          <v-select
            :data-cy="$t('StudyObjectiveForm.objective_level')"
            v-model="form.objectiveLevel"
            :label="$t('StudyObjectiveForm.objective_level')"
            :items="objectiveLevels"
            item-text="sponsorPreferredName"
            return-object
            dense
            clearable
            style="max-width: 400px"
            />
        </v-col>
      </v-row>
    </template>
  </horizontal-stepper-form>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import _isEqual from 'lodash/isEqual'
import { bus } from '@/main'
import { objectManagerMixin } from '@/mixins/objectManager'
import instances from '@/utils/instances'
import statuses from '@/constants/statuses'
import objectives from '@/api/objectives'
import objectiveTemplates from '@/api/objectiveTemplates'
import templateParameterTypes from '@/api/templateParameterTypes'
import defaultParameterValues from '@/utils/defaultParameterValues'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector'
import study from '@/api/study'
import StudySelectionTable from './StudySelectionTable'
import filteringParameters from '@/utils/filteringParameters'
import constants from '@/constants/libraries'

export default {
  mixins: [objectManagerMixin],
  components: {
    HorizontalStepperForm,
    NNParameterHighlighter,
    NNTable,
    NNTemplateInputField,
    ParameterValueSelector,
    StudySelectionTable
  },
  props: {
    studyObjective: {
      type: Object,
      required: false
    },
    currentStudyObjectives: Array
  },
  computed: {
    ...mapGetters({
      objectiveLevels: 'studiesGeneral/objectiveLevels',
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    title () {
      if (this.studyObjective) {
        return this.$t('StudyObjectiveForm.edit_title')
      }
      return this.$t('StudyObjectiveForm.add_title')
    },
    selectedTemplateName () {
      return (this.form.objectiveTemplate) ? this.form.objectiveTemplate.name : ''
    },
    selectedDefaultParameterValues () {
      if (this.form.objectiveTemplate) {
        if (Array.isArray(this.form.objectiveTemplate.defaultParameterValues)) {
          return this.form.objectiveTemplate.defaultParameterValues
        }
      }
      return []
    },
    expandedTemplates () {
      const result = []
      for (const template of this.templates) {
        result.push(template)
        if (defaultParameterValues.hasDefaultParameterValues(template)) {
          for (const setNumber in template.defaultParameterValues) {
            const fakeTemplate = {
              uid: template.uid,
              name: template.name,
              defaultParameterValuesSet: setNumber,
              library: template.library
            }
            fakeTemplate.defaultParameterValues = template.defaultParameterValues[setNumber]
            result.push(fakeTemplate)
          }
        }
      }
      return result
    }
  },
  data () {
    return {
      helpItems: [
        'StudyObjectiveForm.add_title',
        'StudyObjectiveForm.select_mode',
        'StudyObjectiveForm.template_mode',
        'StudyObjectiveForm.scratch_mode',
        'StudyObjectiveForm.select_objective_tpl',
        'StudyObjectiveForm.select_tpl_parameters_label',
        'StudyObjectiveForm.select_studies',
        'StudyObjectiveForm.study_objective',
        'StudyObjectiveForm.objective_level',
        'StudyObjectiveForm.step_edit_title'
      ],
      creationMode: 'select',
      extraStudyObjectiveFilters: {
        'objective.library.name': { v: [constants.LIBRARY_SPONSOR] }
      },
      form: {},
      templateForm: {},
      loadingParameters: false,
      parameters: [],
      apiEndpoint: objectives,
      apiTemplateEndpoint: objectiveTemplates,
      parameterTypes: [],
      alternateSteps: [
        { name: 'creationMode', title: this.$t('StudyObjectiveForm.creation_mode_label') },
        { name: 'selectTemplate', title: this.$t('StudyObjectiveForm.select_tpl_title') },
        { name: 'createObjective', title: this.$t('StudyObjectiveForm.step2_title') },
        { name: 'objectiveLevel', title: this.$t('StudyObjectiveForm.step3_title') }
      ],
      editModeSteps: [
        { name: 'editObjective', title: this.$t('StudyObjectiveForm.step_edit_title') },
        { name: 'objectiveLevel', title: this.$t('StudyObjectiveForm.step3_title') }
      ],
      scratchModeSteps: [
        { name: 'creationMode', title: this.$t('StudyObjectiveForm.creation_mode_label') },
        { name: 'createTemplate', title: this.$t('StudyObjectiveForm.create_template_title') },
        { name: 'createObjective', title: this.$t('StudyObjectiveForm.step2_title') },
        { name: 'objectiveLevel', title: this.$t('StudyObjectiveForm.step3_title') }
      ],
      selectedStudies: [],
      selectedStudyObjectives: [],
      steps: this.getInitialSteps(),
      studies: [],
      templates: [],
      tplHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('_global.indications'), value: 'indications', filteringName: 'indications.name' },
        { text: this.$t('ObjectiveTemplateTable.objective_cat'), value: 'categories' },
        { text: this.$t('ObjectiveTemplateTable.confirmatory_testing'), value: 'confirmatoryTesting' },
        { text: this.$t('_global.template'), value: 'name', width: '30%' }
      ],
      objectiveHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('Study.study_id'), value: 'studyUid' },
        { text: this.$t('StudyObjectiveForm.study_objective'), value: 'objective.name' },
        { text: this.$t('StudyObjectiveForm.objective_level'), value: 'objectiveLevel.sponsorPreferredName' }
      ],
      selectedObjectiveHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('Study.study_id'), value: 'studyId' },
        { text: this.$t('StudyObjectiveForm.study_objective'), value: 'objective.name' },
        { text: this.$t('StudyObjectiveForm.objective_level'), value: 'objectiveLevel.sponsorPreferredName' }
      ],
      options: {},
      total: 0
    }
  },
  methods: {
    close () {
      this.creationMode = 'select'
      this.form = {}
      this.templateForm = {}
      this.parameters = []
      this.$refs.stepper.reset()
      this.selectedStudyObjectives = []
      this.selectedStudies = []
      this.$emit('close')
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    getInitialSteps () {
      return [
        { name: 'creationMode', title: this.$t('StudyObjectiveForm.creation_mode_label') },
        { name: 'selectStudies', title: this.$t('StudyObjectiveForm.select_studies') },
        { name: 'selectObjective', title: this.$t('StudyObjectiveForm.select_objective') }
      ]
    },
    getObjectiveTemplates (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.status = statuses.FINAL
      if (params.filters) {
        params.filters = JSON.parse(params.filters)
      } else {
        params.filters = {}
      }
      Object.assign(params.filters, { 'library.name': { v: [constants.LIBRARY_SPONSOR] } })
      objectiveTemplates.get(params).then(resp => {
        this.templates = resp.data.items
        this.total = resp.data.total
        if (this.studyObjective) {
          this.initFromStudyObjective(this.studyObjective)
        }
      })
    },
    async loadParameters (template) {
      if (template) {
        this.loadingParameters = true
        const resp = await objectiveTemplates.getParameters(template.uid, { study_uid: this.selectedStudy.uid })
        this.parameters = resp.data
        if (template.defaultParameterValues.length) {
          instances.loadParameterValues(template.defaultParameterValues, this.parameters, true)
        }
        this.loadingParameters = false
      } else {
        this.parameters = []
      }
    },
    initFromStudyObjective (studyObjective) {
      this.creationMode = 'template'
      this.form = JSON.parse(JSON.stringify(studyObjective))
      this.showParametersFromObject(studyObjective.objective)
      this.steps = this.editModeSteps
      if (this.templates.length !== 0) {
        this.$set(this.form, 'objectiveTemplate', this.templates.find(
          item => item.uid === this.form.objective.objectiveTemplate.uid))
      }
      this.originalForm = { ...this.form }
    },
    async selectObjectiveTemplate (template) {
      await this.loadParameters(template)
      this.$set(this.form, 'objectiveTemplate', {})
      this.$set(this.form, 'objectiveTemplate', template)
    },
    selectStudyObjective (studyObjective) {
      this.selectedStudyObjectives.push(studyObjective)
      this.$set(this.form, 'objectiveLevel', studyObjective.objectiveLevel)
    },
    unselectStudyObjective (studyObjective) {
      this.selectedStudyObjectives = this.selectedStudyObjectives.filter(item => item.objective.name !== studyObjective.objective.name)
    },
    isStudyObjectiveSelected (studyObjective) {
      let selected = this.selectedStudyObjectives.find(item => item.objective.uid === studyObjective.objective.uid)
      if (!selected && this.currentStudyObjectives.length) {
        selected = this.currentStudyObjectives.find(item => item.objective.uid === studyObjective.objective.uid)
      }
      return selected !== undefined
    },
    getCopyButtonColor (item) {
      return (!this.isStudyObjectiveSelected(item) ? 'primary' : '')
    },
    async createTemplate (step) {
      if (this.creationMode !== 'scratch' || step !== 2) {
        return true
      }
      if (this.form.objectiveTemplate && this.form.objectiveTemplate.name === this.templateForm.name) {
        return true
      }
      const data = { ...this.templateForm, studyUid: this.selectedStudy.uid }
      data.libraryName = 'User Defined'
      try {
        const resp = await objectiveTemplates.create(data)
        await objectiveTemplates.approve(resp.data.uid)
        this.$set(this.form, 'objectiveTemplate', resp.data)
      } catch (error) {
        return false
      }
      this.loadParameters(this.form.objectiveTemplate)
      return true
    },
    async getStudyObjectiveNamePreview () {
      const objectiveData = {
        objectiveTemplateUid: this.form.objective.objectiveTemplate.uid,
        parameterValues: await instances.formatParameterValues(this.parameters),
        libraryName: this.form.objectiveTemplate ? this.form.objectiveTemplate.library.name : this.form.objective.library.name
      }
      const resp = await study.getStudyObjectivePreview(this.selectedStudy.uid, { objectiveData })
      return resp.data.objective.name
    },
    async submit () {
      let action = null
      let notification = null
      let args = null

      if (this.studyObjective) {
        args = {
          studyUid: this.selectedStudy.uid,
          studyObjectiveUid: this.studyObjective.studyObjectiveUid,
          form: JSON.parse(JSON.stringify(this.form))
        }
        const namePreview = await this.getStudyObjectiveNamePreview()
        if (namePreview !== this.studyObjective.objective.name) {
          args.form.parameters = this.parameters
        }
        action = 'studyObjectives/updateStudyObjective'
        notification = 'objective_updated'
      } else if (this.creationMode === 'template' || this.creationMode === 'scratch') {
        args = {
          studyUid: this.selectedStudy.uid,
          form: JSON.parse(JSON.stringify(this.form)),
          parameters: this.parameters
        }
        action = 'studyObjectives/addStudyObjectiveFromTemplate'
        notification = 'objective_added'
      } else {
        for (const item of this.selectedStudyObjectives) {
          args = {
            studyUid: this.selectedStudy.uid,
            objectiveUid: item.objective.uid
          }
          if (this.form.objectiveLevel) {
            args.objectiveLevelUid = this.form.objectiveLevel.termUid
          }
          await this.$store.dispatch('studyObjectives/addStudyObjective', args)
        }
        bus.$emit('notification', { msg: this.$t('StudyObjectiveForm.objective_added') })
        this.close()
        return
      }
      if (this.studyObjective && _isEqual(this.originalForm, args.form)) {
        bus.$emit('notification', { msg: this.$t('_global.no_changes'), type: 'info' })
        this.close()
        return
      }
      this.$store.dispatch(action, args).then(resp => {
        bus.$emit('notification', { msg: this.$t(`StudyObjectiveForm.${notification}`) })
        this.close()
      }).catch(() => {
        this.$refs.stepper.loading = false
      })
    }
  },
  mounted () {
    templateParameterTypes.getTypes().then(resp => {
      this.parameterTypes = resp.data
    })
    study.get({ hasStudyObjective: true }).then(resp => {
      this.studies = resp.data.items.filter(study => study.uid !== this.selectedStudy.uid)
    })
  },
  watch: {
    studyObjective: {
      handler (val) {
        if (val) {
          this.initFromStudyObjective(val)
        }
      },
      immediate: true
    },
    creationMode (value) {
      if (!this.studyObjective) {
        if (value === 'template') {
          this.steps = this.alternateSteps
          this.getObjectiveTemplates()
        } else if (value === 'select') {
          this.steps = this.getInitialSteps()
        } else {
          this.steps = this.scratchModeSteps
        }
      }
    }
  }
}
</script>
<style scoped>
.header-title {
  color: var(--v-secondary-base) !important;
  font-size: large;
}
</style>
