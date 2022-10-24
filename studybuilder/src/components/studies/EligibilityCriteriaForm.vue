<template>
<div>
  <horizontal-stepper-form
    ref="stepper"
    :title="title"
    :steps="steps"
    @close="close"
    @save="submit"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    :extra-step-validation="createTemplate"
    >
    <template v-slot:step.creation_mode>
      <v-radio-group
        v-model="creationMode"
        >
        <v-radio data-cy="criteria-from-study" :label="$t('EligibilityCriteriaForm.select_from_studies')" value="select" />
        <v-radio data-cy="criteria-from-template" :label="$t('EligibilityCriteriaForm.create_from_template')" value="template" />
        <v-radio data-cy="criteria-from-scratch" :label="$t('EligibilityCriteriaForm.create_from_scratch')" value="scratch" />
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
    <template v-slot:step.select>
      <p class="grey--text text-subtitle-1 font-weight-bold">{{ $t('EligibilityCriteriaForm.selected_criteria') }}</p>
      <v-data-table
        :headers="selectionHeaders"
        :items="selectedCriteria"
        >
        <template v-slot:item.name="{ item }">
          <template v-if="item.criteriaTemplate">
            <n-n-parameter-highlighter
              :name="item.criteriaTemplate.name"
              default-color="orange"
              />
          </template>
          <template v-else>
            <n-n-parameter-highlighter
              :name="item.criteria.name"
              :show-prefix-and-postfix="false"
              />
          </template>
        </template>
        <template v-slot:item.guidanceText="{ item }">
          <template v-if="item.criteriaTemplate">
            <span v-html="item.criteriaTemplate.guidanceText" />
          </template>
          <template v-else>
            <span v-html="item.criteria.criteriaTemplate.guidanceText" />
          </template>
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn
            icon
            color="red"
            @click="unselectStudyCriteria(item)"
            >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </template>
    <template v-slot:step.select.after>
      <p class="grey--text text-subtitle-1 font-weight-bold mb-0 ml-3">{{ $t('StudyObjectiveForm.copy_instructions') }}</p>
      <v-col cols="12">
        <study-selection-table
          :headers="stdHeaders"
          data-fetcher-name="getAllStudyCriteria"
          @item-selected="selectTemplate"
          :studies="selectedStudies"
          :extra-data-fetcher-filters="extraDataFetcherFilters"
          >
          <template v-slot:item.name="{ item }">
            <template v-if="item.criteriaTemplate">
              <n-n-parameter-highlighter
                :name="item.criteriaTemplate.name"
                default-color="orange"
                />
            </template>
            <template v-else>
              <n-n-parameter-highlighter
                :name="item.criteria.name"
                :show-prefix-and-postfix="false"
                />
            </template>
          </template>
          <template v-slot:item.guidanceText="{ item }">
            <template v-if="item.criteriaTemplate">
              <span v-html="item.criteriaTemplate.guidanceText" />
            </template>
            <template v-else>
              <span v-html="item.criteria.guidanceText" />
            </template>
          </template>
        </study-selection-table>
      </v-col>
    </template>
    <template v-slot:step.createFromTemplate>
      <v-data-table
        :headers="selectionHeaders"
        :items="selectedCriteria"
        >
        <template v-slot:item.name="{ item }">
          <n-n-parameter-highlighter
            :name="item.name"
            default-color="orange"
            />
        </template>
        <template v-slot:item.guidanceText="{ item }">
          <span v-html="item.guidanceText" />
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn
            icon
            color="red"
            @click="unselectTemplate(item)"
            >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </template>
    <template v-slot:step.createFromTemplate.after>
      <p class="grey--text text-subtitle-1 font-weight-bold mb-0 ml-3">{{ $t('StudyObjectiveForm.copy_instructions') }}</p>
      <v-col cols="12">
        <n-n-table
          key="criteriaTemplateTable"
          :headers="tplHeaders"
          :items="criteriaTemplates"
          :items-per-page="15"
          hide-default-switches
          hide-actions-menu
          elevation="0"
          :options.sync="options"
          :server-items-length="total"
          has-api
          column-data-resource="criteria-templates"
          @filter="getCriteriaTemplates"
          >
          <template v-slot:item.indications="{ item }">
            <template v-if="item.indications">
              {{ item.indications|names }}
            </template>
             <template v-else>
              {{ $t('_global.not_applicable_long') }}
             </template>
          </template>
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
          <template v-slot:item.name="{ item }">
            <n-n-parameter-highlighter :name="item.name" default-color="orange" />
          </template>
          <template v-slot:item.guidanceText="{ item }">
            <span v-html="item.guidanceText" />
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              :data-cy="$t('StudyObjectiveForm.copy_template')"
              icon
              color="primary"
              @click="selectTemplate(item)"
              :title="$t('StudyObjectiveForm.copy_template')">
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
          </template>
        </n-n-table>
      </v-col>
    </template>
    <template v-slot:step.createFromScratch="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-row>
            <v-col>
              <n-n-template-input-field
                :data-cy="$t('EligibilityCriteriaForm.criteria_template')"
                v-model="form.name"
                :label="$t('EligibilityCriteriaForm.criteria_template')"
                :items="parameterTypes"
                :error-messages="errors"
                :show-drop-down-early="true"
                />
            </v-col>
          </v-row>
        </validation-provider>
      </validation-observer>
      <v-row>
        <v-col>
          <vue-editor
            ref="editor"
            id="editor"
            v-model="form.guidanceText"
            :editor-toolbar="customToolbar"
            :placeholder="$t('CriteriaTemplateForm.guidance_text')"
            class="pt-4"
            />
        </v-col>
      </v-row>
    </template>
    <template v-slot:step.createCriteria="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <parameter-value-selector
          v-if="form.criteriaTemplate"
          :value="parameters"
          :template="form.criteriaTemplate.name"
          color="white"
          />
      </validation-observer>
    </template>
  </horizontal-stepper-form>
</div>
</template>

<script>
import { bus } from '@/main'
import templateParameterTypes from '@/api/templateParameterTypes'
import criteriaTemplates from '@/api/criteriaTemplates'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import instances from '@/utils/instances'
import { mapGetters } from 'vuex'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector'
import study from '@/api/study'
import StudySelectionTable from './StudySelectionTable'
import filteringParameters from '@/utils/filteringParameters'
import statuses from '@/constants/statuses'
import { VueEditor } from 'vue2-editor'

export default {
  components: {
    HorizontalStepperForm,
    NNParameterHighlighter,
    NNTable,
    NNTemplateInputField,
    ParameterValueSelector,
    StudySelectionTable,
    VueEditor
  },
  props: {
    criteriaType: Object
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    title () {
      return this.$t('_global.add') + ' ' + this.criteriaType.sponsorPreferredNameSentenceCase
    }
  },
  data () {
    return {
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }]
      ],
      helpItems: [
        'EligibilityCriteriaForm.add_criteria',
        'EligibilityCriteriaForm.select_from_studies',
        'EligibilityCriteriaForm.create_from_template',
        'EligibilityCriteriaForm.create_from_scratch',
        'EligibilityCriteriaForm.select_criteria_templates'
      ],
      creationMode: 'select',
      extraDataFetcherFilters: {
        'criteria.library.name': { v: ['Sponsor'] },
        'criteriaType.sponsorPreferredName': { v: [this.criteriaType.sponsorPreferredName] }
      },
      tplHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('_global.indications'), value: 'indications', filteringName: 'indications.name' },
        { text: this.$t('EligibilityCriteriaForm.criterion_cat'), value: 'categories', filteringName: 'categories.name.sponsorPreferredName' },
        { text: this.$t('EligibilityCriteriaForm.criterion_sub_cat'), value: 'subCategories', filteringName: 'subCategories.name.sponsorPreferredName' },
        { text: this.$t('EligibilityCriteriaForm.criteria_template'), value: 'name' },
        { text: this.$t('EligibilityCriteriaForm.guidance_text'), value: 'guidanceText' }
      ],
      criteriaTemplates: [],
      form: {},
      loadingParameters: false,
      parameters: [],
      parameterTypes: [],
      selectedCriteria: [],
      selectedStudies: [],
      steps: this.getInitialSteps(),
      studies: [],
      createFromTemplateSteps: [
        { name: 'creation_mode', title: this.$t('EligibilityCriteriaForm.creation_mode_label') },
        { name: 'createFromTemplate', title: this.$t('EligibilityCriteriaForm.select_criteria_templates') }
      ],
      createFromScratchSteps: [
        { name: 'creation_mode', title: this.$t('EligibilityCriteriaForm.creation_mode_label') },
        { name: 'createFromScratch', title: this.$t('EligibilityCriteriaForm.create_from_scratch'), noStyle: true },
        { name: 'createCriteria', title: this.$t('EligibilityCriteriaForm.create_criteria') }
      ],
      selectionHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('EligibilityCriteriaForm.criteria_text'), value: 'name', class: 'text-center' },
        { text: this.$t('EligibilityCriteriaForm.guidance_text'), value: 'guidanceText' }
      ],
      stdHeaders: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('Study.study_id'), value: 'studyUid' },
        { text: this.$t('EligibilityCriteriaForm.criteria_text'), value: 'name' },
        { text: this.$t('EligibilityCriteriaForm.guidance_text'), value: 'guidanceText' }
      ],
      options: {},
      total: 0
    }
  },
  mounted () {
    templateParameterTypes.getTypes().then(resp => {
      this.parameterTypes = resp.data
    })
    study.get({ hasStudyCriteria: true }).then(resp => {
      this.studies = resp.data.items.filter(study => study.uid !== this.selectedStudy.uid)
    })
  },
  methods: {
    close () {
      this.$emit('close')
      this.$refs.stepper.reset()
      this.steps = this.getInitialSteps()
      this.creationMode = 'select'
      this.form = {}
      this.selectedStudies = []
      this.selectedCriteria = []
    },
    getInitialSteps () {
      return [
        { name: 'creation_mode', title: this.$t('EligibilityCriteriaForm.creation_mode_label') },
        { name: 'selectStudies', title: this.$t('EligibilityCriteriaForm.select_studies') },
        { name: 'select', title: this.$t('EligibilityCriteriaForm.select_criteria') }
      ]
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    getCriteriaTemplates (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.status = statuses.FINAL
      if (params.filters) {
        params.filters = JSON.parse(params.filters)
      } else {
        params.filters = {}
      }
      Object.assign(params.filters, { 'type.name.sponsorPreferredNameSentenceCase': { v: [this.criteriaType.sponsorPreferredNameSentenceCase] } })
      criteriaTemplates.get(params).then(resp => {
        this.criteriaTemplates = resp.data.items
        this.total = resp.data.total
      })
    },
    selectTemplate (template) {
      this.selectedCriteria.push(template)
    },
    unselectTemplate (template) {
      this.selectedCriteria = this.selectedCriteria.filter(item => item.name !== template.name)
    },
    unselectStudyCriteria (studyCriteria) {
      this.selectedCriteria = this.selectedCriteria.filter(item => item.studyCriteriaUid !== studyCriteria.studyCriteriaUid)
    },
    async loadParameters (template) {
      if (template) {
        this.loadingParameters = true
        const resp = await criteriaTemplates.getObjectTemplateParameters(template.uid)
        this.parameters = resp.data
        this.loadingParameters = false
      } else {
        this.parameters = []
      }
    },
    async createTemplate (step) {
      if (this.creationMode !== 'scratch' || step !== 2) {
        return true
      }
      const data = {
        ...this.form,
        libraryName: 'User Defined',
        typeUid: this.criteriaType.termUid,
        studyUid: this.selectedStudy.uid
      }
      try {
        const resp = await criteriaTemplates.create(data)
        await criteriaTemplates.approve(resp.data.uid)
        this.$set(this.form, 'criteriaTemplate', resp.data)
      } catch (error) {
        return false
      }
      this.loadParameters(this.form.criteriaTemplate)
      return true
    },
    async submit () {
      if (this.creationMode !== 'scratch') {
        if (!this.selectedCriteria.length) {
          return
        }
        if (this.creationMode === 'template') {
          const data = []
          for (const criteria of this.selectedCriteria) {
            data.push({
              criteriaTemplateUid: criteria.uid,
              libraryName: criteria.library.name
            })
          }
          await study.batchCreateStudyCriteria(this.selectedStudy.uid, data)
        } else {
          const data = []
          for (const studyCriteria of this.selectedCriteria) {
            if (studyCriteria.criteriaTemplate) {
              data.push({
                criteriaTemplateUid: studyCriteria.criteriaTemplate.uid,
                libraryName: studyCriteria.criteriaTemplate.library.name
              })
            } else {
              const payload = {
                criteriaData: {
                  parameterValues: studyCriteria.criteria.parameterValues,
                  criteriaTemplateUid: studyCriteria.criteria.criteriaTemplate.uid,
                  libraryName: studyCriteria.criteria.library.name
                }
              }
              await study.createStudyCriteria(this.selectedStudy.uid, payload)
            }
          }
          await study.batchCreateStudyCriteria(this.selectedStudy.uid, data)
        }
      } else {
        const data = {
          criteriaData: {
            criteriaTemplateUid: this.form.criteriaTemplate.uid,
            parameterValues: await instances.formatParameterValues(this.parameters),
            libraryName: 'Sponsor' // FIXME
          }
        }
        await study.createStudyCriteria(this.selectedStudy.uid, data)
      }
      bus.$emit('notification', { type: 'success', msg: this.$t('EligibilityCriteriaForm.add_success') })
      this.$emit('added')
      this.close()
    }
  },
  watch: {
    creationMode (value) {
      if (value === 'select') {
        this.steps = this.getInitialSteps()
      } else if (value === 'template') {
        this.steps = this.createFromTemplateSteps
        this.getCriteriaTemplates()
      } else {
        this.steps = this.createFromScratchSteps
      }
    }
  }
}
</script>
