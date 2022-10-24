<template>
<div>
  <horizontal-stepper-form
    ref="stepper"
    :title="title"
    :steps="steps"
    @close="close"
    @save="submit"
    :form-observer-getter="getObserver"
    :editable="studyEndpoint !== undefined && studyEndpoint !== null"
    :extra-step-validation="extraStepValidation"
    :helpItems="helpItems"
    :editData="form"
    >
    <template v-slot:step.creationMode>
      <v-radio-group
        v-model="creationMode"
        >
        <v-radio class="mt-2" :label="$t('StudyEndpointForm.template_mode')" value="template" />
        <v-radio :label="$t('StudyEndpointForm.scratch_mode')" value="scratch" />
      </v-radio-group>
    </template>
    <template v-slot:step.objective>
      <v-card flat>
        <v-card-text>
          <v-row>
            <v-col cols="10" class="parameterBackground">
              <n-n-parameter-highlighter
                :name="selectedStudyObjectiveName"
                default-color="orange"
                />
            </v-col>
            <v-col cols="2">
              <v-checkbox
                v-model="selectLater"
                :label="$t('StudyEndpointForm.select_later')"
                @change="onSelectLaterChange"
                hide-details
                />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </template>
    <template v-slot:step.objective.after>
      <p class="grey--text text-subtitle-1 font-weight-bold mb-0 ml-3 mt-2">{{ $t('StudyObjectiveForm.copy_instructions') }}</p>
      <v-col cols="12" class="pt-0">
        <n-n-table
          key="objectivesTable"
          :headers="objectiveHeaders"
          :items="objectives"
          hide-default-switches
          hide-actions-menu
          :items-per-page="15"
          elevation="0"
          >
          <template v-slot:item.objective.name="{ item }">
            <n-n-parameter-highlighter :name="item.objective.name" />
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              :data-cy="$t('StudyEndpointForm.copy_objective')"
              icon
              color="primary"
              @click="selectStudyObjective(item)"
              :title="$t('StudyEndpointForm.copy_objective')">
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
          </template>
        </n-n-table>
      </v-col>
    </template>

    <template v-slot:step.selectEndpointTemplate>
      <v-card flat class="parameterBackground">
        <v-card-text>
          <n-n-parameter-highlighter :name="selectedEndpointTemplateName" default-color="orange" />
        </v-card-text>
      </v-card>
    </template>

    <template v-slot:step.selectEndpointTemplate.after>
      <p class="grey--text text-subtitle-1 mt-4 font-weight-bold ml-3">{{ $t('StudyObjectiveForm.copy_instructions') }}</p>
      <v-col cols="12" class="pt-0">
        <n-n-table
          key="templateTable"
          :headers="tplHeaders"
          :items="endpointTemplates"
          hide-default-switches
          hide-actions-menu
          :items-per-page="15"
          :options.sync="options"
          :server-items-length="total"
          has-api
          :column-data-resource="`endpoint-templates`"
          @filter="getEndpointTemplates"
          show-filter-bar-by-default
          >
          <template v-slot:item.categories="{ item }">
            <template v-if="item.categories">
              {{ item.categories|terms }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template v-slot:item.subCategories="{ item }">
            <template v-if="item.subCategories">
              {{ item.subCategories|terms }}
            </template>
            <template v-else>
              {{ $t('_global.not_applicable_long') }}
            </template>
          </template>
          <template v-slot:item.indications="{ item }">
            <template v-if="item.indications">
              {{ item.indications|names }}
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
              icon
              color="primary"
              @click="selectEndpointTemplate(item)"
              :title="$t('StudyObjectiveForm.copy_template')">
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
          </template>
        </n-n-table>
      </v-col>
    </template>

    <template v-slot:step.endpointDetails="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <v-progress-circular
          v-if="loadingEndpointParameters"
          indeterminate
          color="secondary"
          />
        <v-row>
          <v-col cols="5">
            <parameter-value-selector
              v-if="form.endpointTemplate !== undefined"
              ref="endpointParamSelector"
              :value="endpointTemplateParameters"
              :template="form.endpointTemplate.name"
              color="white"
              :previewText="$t('StudyEndpointForm.endpoint_title')"
              stacked
              />
          </v-col>
          <v-col cols="2" class="px-0">
            <p class="grey--text text-subtitle-1 font-weight-bold my-2">{{ $t('StudyEndpointForm.selected_endpoint_units') }}</p>
            <v-card flat class="parameterBackground">
              <v-card-text>
                <n-n-parameter-highlighter :name="unitsDisplay(form.endpointUnits.units)" />
              </v-card-text>
            </v-card>
            <v-row class="mt-5">
              <v-col cols="8">
                <validation-provider
                  v-slot="{ errors }"
                  :rules="`requiredIfNotNA:${skipUnits}`"
                  >
                  <multiple-select
                    v-model="form.endpointUnits.units"
                    :label="$t('StudyEndpointForm.units')"
                    :items="units"
                    :errors="errors"
                    item-text="name"
                    item-value="uid"
                    :disabled="skipUnits"
                    />
                </validation-provider>
              </v-col>
              <v-col v-if="form.endpointUnits.units && form.endpointUnits.units.length > 1">
                <v-select
                  v-model="form.endpointUnits.separator"
                  :label="$t('StudyEndpointForm.separator')"
                  :items="separators"
                  clearable
                  />
              </v-col>
              <v-col cols="2">
                <validation-provider
                  name="skipUnits"
                  rules=""
                  >
                  <v-btn
                    icon
                    class="ml-n4"
                    @click="clearUnits"
                  >
                    <v-icon v-if="!skipUnits">mdi-eye-outline</v-icon>
                    <v-icon v-else>mdi-eye-off-outline</v-icon>
                  </v-btn>
                </validation-provider>
              </v-col>
            </v-row>
          </v-col>
          <v-col cols="5">
            <parameter-value-selector
              :value="timeframeTemplateParameters"
              color="white"
              :previewText="$t('StudyEndpointForm.timeframe')"
              v-if="!form.timeframeTemplate"
              />
            <parameter-value-selector
              ref="timeframeParamSelector"
              :value="timeframeTemplateParameters"
              :template="form.timeframeTemplate.name"
              color="white"
              :previewText="$t('StudyEndpointForm.timeframe')"
              v-if="form.timeframeTemplate && timeframeTemplateParameters.length"
              stacked
              />
            <v-progress-circular
              v-if="loadingTimeframeParameters"
              indeterminate
              color="secondary"
              />
          </v-col>
        </v-row>
      </validation-observer>
    </template>

    <template v-slot:step.createEndpointTemplate="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules=""
          >
          <n-n-template-input-field
            v-model="endpointTemplateForm.name"
            :label="$t('EndpointTemplateForm.name')"
            :items="parameterTypes"
            :error-messages="errors"
            show-drop-down-early
            @input="watchEndpointTemplate()"
            />
        </validation-provider>
      </validation-observer>
    </template>

    <template v-slot:step.selectTimeframe="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <v-row class="align-center">
          <v-col cols="10">
            <validation-provider
              v-slot="{ errors }"
              rules=""
              >
              <v-autocomplete
                v-model="form.timeframeTemplate"
                :label="$t('StudyEndpointForm.timeframe_template')"
                :items="timeframeTemplates"
                item-text="namePlain"
                return-object
                :error-messages="errors"
                clearable
                append-icon="mdi-magnify"
                @change="loadTimeframeTemplateParameters"
                :disabled="selectTimeFrameLater"
                />
            </validation-provider>
          </v-col>
          <v-col cols="2">
            <validation-provider>
              <v-checkbox
                v-model="selectTimeFrameLater"
                :label="$t('StudyEndpointForm.select_later')"
                @change="onSelectTimeFrameLaterChange"
                hide-details
                />
            </validation-provider>
          </v-col>
        </v-row>
      </validation-observer>
    </template>

    <template v-slot:step.level="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules=""
          >
          <v-select
            v-model="form.endpointLevel"
            :label="$t('StudyEndpointForm.endpoint_level')"
            :items="endpointLevels"
            item-text="sponsorPreferredName"
            return-object
            :error-messages="errors"
            clearable
            style="max-width: 400px"
            />
        </validation-provider>
      </validation-observer>
      <v-select
        v-model="form.endpointSubLevel"
        :label="$t('StudyEndpointForm.endpoint_sub_level')"
        :items="endpointSubLevels"
        item-text="sponsorPreferredName"
        return-object
        clearable
        style="max-width: 400px"
        />
    </template>
  </horizontal-stepper-form>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import endpoints from '@/api/endpoints'
import endpointTemplates from '@/api/endpointTemplates'
import study from '@/api/study'
import templateParameterTypes from '@/api/templateParameterTypes'
import timeframes from '@/api/timeframes'
import timeframeTemplates from '@/api/timeframeTemplates'
import instances from '@/utils/instances'
import statuses from '@/constants/statuses'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import MultipleSelect from '@/components/tools/MultipleSelect'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector'
import _isEqual from 'lodash/isEqual'
import filteringParameters from '@/utils/filteringParameters'
import constants from '@/constants/libraries'

export default {
  components: {
    HorizontalStepperForm,
    MultipleSelect,
    ParameterValueSelector,
    NNParameterHighlighter,
    NNTable,
    NNTemplateInputField
  },
  props: ['studyEndpoint'],
  computed: {
    ...mapGetters({
      endpointLevels: 'studiesGeneral/endpointLevels',
      endpointSubLevels: 'studiesGeneral/endpointSubLevels',
      selectedStudy: 'studiesGeneral/selectedStudy',
      units: 'studiesGeneral/allUnits'
    }),
    title () {
      if (this.studyEndpoint) {
        return this.$t('StudyEndpointForm.edit_title')
      }
      return this.$t('StudyEndpointForm.add_title')
    },
    studyObjectiveLevel () {
      if (this.form.studyObjective && this.form.studyObjective.objectiveLevel) {
        return this.form.studyObjective.objectiveLevel.sponsorPreferredName
      }
      return ''
    },
    selectedStudyObjectiveName () {
      return (this.form.studyObjective) ? this.form.studyObjective.objective.name : ''
    },
    selectedEndpointTemplateName () {
      return (this.form.endpointTemplate) ? this.form.endpointTemplate.name : ''
    },
    selectedStudyEndpointUnits () {
      if (this.form.selectedStudyEndpoint) {
        if (this.form.selectedStudyEndpoint.endpointUnits.units.length > 1) {
          return this.form.selectedStudyEndpoint.endpointUnits.units.join(this.form.selectedStudyEndpoint.endpointUnits.separator)
        }
        return this.form.selectedStudyEndpoint.endpointUnits.units[0]
      }
      return ''
    }
  },
  data () {
    return {
      helpItems: [
        'StudyEndpointForm.template_mode',
        'StudyEndpointForm.scratch_mode',
        'StudyEndpointForm.select_objective_title',
        'StudyEndpointForm.step2_title',
        'StudyEndpointForm.timeframe_template',
        'StudyEndpointForm.step3_title',
        'StudyEndpointForm.endpoint_level'
      ],
      creationMode: 'template',
      endpointTemplates: [],
      endpointTemplateForm: {},
      endpointTemplateParameters: [],
      form: this.getInitialForm(),
      loadingEndpointParameters: false,
      loadingTimeframeParameters: false,
      objectiveHeaders: [
        { text: this.$t('_global.actions'), value: 'actions' },
        { text: this.$t('_global.name'), value: 'objective.name' },
        { text: this.$t('StudyEndpointForm.objective_level'), value: 'objectiveLevel.sponsorPreferredName' }
      ],
      objectives: [],
      parameterTypes: [],
      selectLater: false,
      selectTimeFrameLater: false,
      separators: ['and', 'or', ','],
      steps: [],
      templateSteps: [
        { name: 'creationMode', title: this.$t('StudyEndpointForm.creation_mode_title') },
        { name: 'objective', title: this.$t('StudyEndpointForm.select_objective_title') },
        { name: 'selectEndpointTemplate', title: this.$t('StudyEndpointForm.step2_title') },
        { name: 'selectTimeframe', title: this.$t('StudyEndpointForm.select_timeframe_title') },
        { name: 'endpointDetails', title: this.$t('StudyEndpointForm.step3_title') },
        { name: 'level', title: this.$t('StudyEndpointForm.endpoint_level_title') }
      ],
      scratchSteps: [
        { name: 'creationMode', title: this.$t('StudyEndpointForm.creation_mode_title') },
        { name: 'objective', title: this.$t('StudyEndpointForm.select_objective_title') },
        { name: 'createEndpointTemplate', title: this.$t('StudyEndpointForm.create_tpl_title') },
        { name: 'selectTimeframe', title: this.$t('StudyEndpointForm.select_timeframe_title') },
        { name: 'endpointDetails', title: this.$t('StudyEndpointForm.step3_title') },
        { name: 'level', title: this.$t('StudyEndpointForm.endpoint_level_title') }
      ],
      editSteps: [
        { name: 'objective', title: this.$t('StudyEndpointForm.select_objective_title') },
        { name: 'selectTimeframe', title: this.$t('StudyEndpointForm.select_timeframe_title') },
        { name: 'endpointDetails', title: this.$t('StudyEndpointForm.step3_title') },
        { name: 'level', title: this.$t('StudyEndpointForm.endpoint_level_title') }
      ],
      skipUnits: false,
      timeframeTemplates: [],
      timeframeTemplateParameters: [],
      tplHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('_global.indications'), value: 'indications', filteringName: 'indications.name' },
        { text: this.$t('EndpointTemplateTable.endpoint_cat'), value: 'categories' },
        { text: this.$t('EndpointTemplateTable.endpoint_sub_cat'), value: 'subCategories' },
        { text: this.$t('_global.template'), value: 'name', width: '30%' }
      ],
      options: {},
      total: 0,
      endpointTitleWarning: false
    }
  },
  methods: {
    watchEndpointTemplate () {
      if (this.endpointTemplateForm.name.length > 254 && !this.endpointTitleWarning) {
        bus.$emit('notification', { msg: this.$t('StudyEndpointForm.endpoint_title_warning'), type: 'warning' })
        this.endpointTitleWarning = true
      }
    },
    unitsDisplay (units) {
      let result = ''
      if (units) {
        units.forEach(uid => {
          result += this.units.find(u => u.uid === uid).name + ', '
        })
      }
      return result.slice(0, -2)
    },
    getInitialForm () {
      return {
        endpointUnits: {}
      }
    },
    close () {
      this.$emit('close')
      this.form = this.getInitialForm()
      this.endpointTemplateForm = {}
      this.creationMode = 'template'
      this.steps = this.templateSteps
      this.$refs.stepper.reset()
      this.skipUnits = false
      this.endpointTitleWarning = false
    },
    clearUnits () {
      this.$set(this.form.endpointUnits, 'units', [])
      this.skipUnits = !this.skipUnits
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    initFromStudyEndpoint (studyEndpoint) {
      this.steps = this.editSteps
      this.form = JSON.parse(JSON.stringify(studyEndpoint))
      if (!studyEndpoint.studyObjective) {
        this.selectLater = true
      }
      if (!studyEndpoint.timeframe) {
        this.selectTimeFrameLater = true
      }
    },
    loadEndpointTemplateParameters (template) {
      this.endpointTemplateParameters = []
      if (template) {
        this.loadingEndpointParameters = true
        endpointTemplates.getParameters(template.uid).then(resp => {
          this.endpointTemplateParameters = resp.data
          this.loadingEndpointParameters = false
        })
      }
    },
    loadTimeframeTemplateParameters (template) {
      this.timeframeTemplateParameters = []
      if (template) {
        this.loadingTimeframeParameters = true
        timeframeTemplates.getParameters(template.uid, { study_uid: this.selectedStudy.uid }).then(resp => {
          this.timeframeTemplateParameters = resp.data
          this.loadingTimeframeParameters = false
        })
      }
    },
    async getStudyEndpointNamePreview () {
      const endpointData = {
        endpointTemplateUid: this.form.endpointTemplate.uid,
        parameterValues: await instances.formatParameterValues(this.endpointTemplateParameters),
        libraryName: this.form.endpointTemplate.library.name
      }
      const resp = await study.getStudyEndpointPreview(this.selectedStudy.uid, { endpointData })
      return resp.data.endpoint.name
    },
    async submit () {
      let args = null
      let action = null
      let notification = null

      if (!this.studyEndpoint) {
        args = {
          studyUid: this.selectedStudy.uid,
          data: JSON.parse(JSON.stringify(this.form)),
          endpointParameters: this.endpointTemplateParameters,
          timeframeParameters: this.timeframeTemplateParameters
        }
        action = 'studyEndpoints/addStudyEndpoint'
        notification = 'endpoint_added'
      } else {
        args = {
          studyUid: this.selectedStudy.uid,
          studyEndpointUid: this.studyEndpoint.studyEndpointUid,
          form: JSON.parse(JSON.stringify(this.form))
        }
        const namePreview = await this.getStudyEndpointNamePreview()
        if (this.studyEndpoint.endpoint.name !== namePreview) {
          args.form.endpointParameters = this.endpointTemplateParameters
        }
        if (
          !this.studyEndpoint.timeframe ||
            (this.studyEndpoint.timeframe && (this.studyEndpoint.timeframe.name !== this.$refs.timeframeParamSelector.namePreview))
        ) {
          args.form.timeframeParameters = this.timeframeTemplateParameters
          args.form.timeframeNamePreview = this.$refs.timeframeParamSelector.namePreview
        }
        action = 'studyEndpoints/updateStudyEndpoint'
        notification = 'endpoint_updated'
      }
      if (this.studyEndpoint) {
        const endpointLevelChanged = !_isEqual(this.form.endpointLevel, this.studyEndpoint.endpointLevel)
        const unitsChanged = !_isEqual(this.form.endpointUnits, this.studyEndpoint.endpointUnits)
        const objectiveDefined = !this.studyObjective && this.form.studyObjective !== undefined

        if (_isEqual(this.form, args.form) && !endpointLevelChanged && !unitsChanged && !objectiveDefined) {
          bus.$emit('notification', { msg: this.$t('_global.no_changes'), type: 'info' })
          this.close()
          return
        }
      }
      this.$store.dispatch(action, args).then(resp => {
        bus.$emit('notification', { msg: this.$t(`StudyEndpointForm.${notification}`) })
        if (action !== 'studyEndpoints/updateStudyEndpoint') {
          this.$emit('created')
        }
        this.close()
      }).catch(() => {
        this.$refs.stepper.loading = false
      })
    },
    loadEndpointTemplate () {
      if (!this.form.endpoint && !this.form.endpointTemplate) {
        return
      }
      this.$set(this.form, 'endpointTemplate', this.endpointTemplates.find(
        item => item.uid === this.form.endpoint.endpointTemplate.uid)
      )
      endpoints.getObjectParameters(this.form.endpoint.uid).then(resp => {
        this.endpointTemplateParameters = resp.data
        instances.loadParameterValues(this.form.endpoint.parameterValues, this.endpointTemplateParameters)
      })
    },
    loadTimeframeTemplate () {
      if (!this.form.timeframe) {
        return
      }
      this.$set(this.form, 'timeframeTemplate', this.timeframeTemplates.find(
        item => item.uid === this.form.timeframe.timeframeTemplate.uid)
      )
      timeframes.getObjectParameters(this.form.timeframe.uid, { study_uid: this.selectedStudy.uid }).then(resp => {
        this.timeframeTemplateParameters = resp.data
        instances.loadParameterValues(this.form.timeframe.parameterValues, this.timeframeTemplateParameters)
      })
    },
    selectStudyObjective (value) {
      this.$set(this.form, 'studyObjective', value)
    },
    onSelectLaterChange (value) {
      if (value) {
        this.$set(this.form, 'studyObjective', null)
      }
    },
    onSelectTimeFrameLaterChange (value) {
      if (value) {
        this.$set(this.form, 'timeframeTemplate', null)
        this.timeframeTemplateParameters = []
      }
    },
    selectEndpointTemplate (template) {
      this.$set(this.form, 'endpointTemplate', template)
      this.loadEndpointTemplateParameters(template)
    },
    selectStudyEndpoint (studyEndpoint) {
      this.$set(this.form, 'selectedStudyEndpoint', studyEndpoint)
    },
    async extraStepValidation (step) {
      if (this.creationMode === 'scratch') {
        if (step !== 3) {
          return true
        }
        if (this.form.endpointTemplate && this.form.endpointTemplate.name === this.endpointTemplateForm.name) {
          return true
        }
        const data = { ...this.endpointTemplateForm, studyUid: this.selectedStudy.uid }
        data.libraryName = constants.LIBRARY_USER_DEFINED
        try {
          const resp = await endpointTemplates.create(data)
          await endpointTemplates.approve(resp.data.uid)
          this.$set(this.form, 'endpointTemplate', resp.data)
        } catch (error) {
          return false
        }
        this.loadEndpointTemplateParameters(this.form.endpointTemplate)
        return true
      }
      if (step === 2) {
        if (this.selectLater || this.form.studyObjective !== undefined) {
          return true
        }
        bus.$emit('notification', { type: 'error', msg: this.$t('StudyEndpointForm.select_objective') })
        return false
      }
      if (step === 3) {
        if (!this.form.endpointTemplate) {
          bus.$emit('notification', { type: 'error', msg: this.$t('StudyEndpointForm.no_endpoint_template') })
          return false
        }
      }
      return true
    },
    getEndpointTemplates (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      if (params.filters) {
        params.filters = JSON.parse(params.filters)
      } else {
        params.filters = {}
      }
      if (!this.studyEndpoint) {
        params.status = statuses.FINAL
        Object.assign(params.filters, { 'library.name': { v: [constants.LIBRARY_SPONSOR] } })
      }
      endpointTemplates.get(params).then(resp => {
        this.endpointTemplates = resp.data.items
        this.total = resp.data.total
      })
    },
    getTimeframeTemplates () {
      const params = {
        filters: { 'library.name': { v: [constants.LIBRARY_SPONSOR] } },
        status: statuses.FINAL
      }
      timeframeTemplates.get(params).then(resp => {
        this.timeframeTemplates = resp.data.items
      })
    }
  },
  created () {
    this.steps = this.templateSteps
  },
  mounted () {
    study.getStudyObjectives(this.selectedStudy.uid).then(resp => {
      this.objectives = resp.data.items
    })
    if (this.studyEndpoint) {
      this.initFromStudyEndpoint(this.studyEndpoint)
    }
    this.getEndpointTemplates()
    this.getTimeframeTemplates()
    templateParameterTypes.getTypes().then(resp => {
      this.parameterTypes = resp.data
    })
  },
  watch: {
    studyEndpoint (val) {
      this.getEndpointTemplates()
      if (val) {
        this.initFromStudyEndpoint(val)
        this.getEndpointTemplates()
        this.getTimeframeTemplates()
      } else {
        this.form = this.getInitialForm()
      }
    },
    creationMode (value) {
      if (!this.studyEndpoint) {
        if (value === 'template') {
          this.steps = this.templateSteps
        } else {
          this.steps = this.scratchSteps
        }
      }
    },
    endpointTemplates (value) {
      if (value && value.length && this.studyEndpoint) {
        this.loadEndpointTemplate()
      }
    },
    timeframeTemplates (value) {
      if (value && value.length && this.studyEndpoint) {
        this.loadTimeframeTemplate()
      }
    },
    endpointTemplateParameters (value) {
      value.forEach(el => {
        if (el.name === 'TextValue' && el.selectedValues && el.selectedValues.length) {
          value[value.indexOf(el)].selectedValues = el.selectedValues[0].name
        }
      })
    },
    timeframeTemplateParameters (value) {
      value.forEach(el => {
        if (el.name === 'TextValue' && el.selectedValues && el.selectedValues.length) {
          value[value.indexOf(el)].selectedValues = el.selectedValues[0].name
        }
      })
    }
  }
}
</script>

<style scoped lang="scss">
.v-stepper {
  background-color: var(--v-dfltBackground-base) !important;
  box-shadow: none;
}
</style>
