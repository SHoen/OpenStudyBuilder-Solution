<template>
<div>
  <horizontal-stepper-form
    ref="stepper"
    :title="$t('EligibilityCriteriaEditForm.title')"
    :steps="steps"
    @close="close"
    @save="submit"
    :form-observer-getter="getObserver"
    editable
    :helpText="$t('_help.StudyObjectiveTable.general')"
    >
    <template v-slot:step.editCriteria="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <parameter-value-selector
          :value="parameters"
          :template="template.name"
          color="white"
          preview-text=" "
          />
      </validation-observer>
    </template>
  </horizontal-stepper-form>
</div>
</template>

<script>
import { bus } from '@/main'
import criteria from '@/api/criteria'
import criteriaTemplates from '@/api/criteriaTemplates'
import instances from '@/utils/instances'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import { mapGetters } from 'vuex'
import { objectManagerMixin } from '@/mixins/objectManager'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector'
import study from '@/api/study'

export default {
  mixins: [objectManagerMixin],
  props: {
    studyCriteria: Object
  },
  components: {
    ParameterValueSelector,
    HorizontalStepperForm
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    template () {
      if (this.studyCriteria.criteriaTemplate) {
        return this.studyCriteria.criteriaTemplate
      }
      return this.studyCriteria.criteria.criteriaTemplate
    },
    library () {
      if (this.studyCriteria.criteriaTemplate) {
        return this.studyCriteria.criteriaTemplate.library
      }
      return this.studyCriteria.criteria.library
    }
  },
  data () {
    return {
      apiEndpoint: criteria,
      helpItems: [],
      loadingParameters: false,
      parameters: [],
      steps: [
        { name: 'editCriteria', title: this.$t('EligibilityCriteriaEditForm.step_title') }
      ]
    }
  },
  methods: {
    close () {
      this.$refs.observer_1.reset()
      this.working = false
      this.$refs.stepper.loading = false
      this.$emit('close')
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    loadTemplateParameters () {
      this.parameters = []
      this.loadingParameters = true
      criteriaTemplates.getParameters(this.template.uid).then(resp => {
        this.parameters = resp.data
        this.loadingParameters = false
        if (this.studyCriteria.criteria) {
          this.showParametersFromObject(this.studyCriteria.criteria)
        }
      })
    },
    async getStudyCriteriaNamePreview () {
      const criteriaData = {
        criteriaTemplateUid: this.studyCriteria.criteria.criteriaTemplate.uid,
        parameterValues: await instances.formatParameterValues(this.parameters),
        libraryName: this.studyCriteria.criteria.library.name
      }
      const resp = await study.getStudyCriteriaPreview(this.selectedStudy.uid, { criteriaData })
      return resp.data.criteria.name
    },
    async submit () {
      const valid = await this.$refs.observer_1.validate()
      if (!valid) {
        return
      }
      if (this.studyCriteria.criteria) {
        const namePreview = await this.getStudyCriteriaNamePreview()
        if (namePreview === this.studyCriteria.criteria.name) {
          bus.$emit('notification', { msg: this.$t('_global.no_changes'), type: 'info' })
          this.close()
          return
        }
      }
      const parameterValues = await instances.formatParameterValues(this.parameters)
      const data = {
        criteriaTemplateUid: this.template.uid,
        parameterValues,
        libraryName: this.library.name
      }
      await study.patchStudyCriteria(this.selectedStudy.uid, this.studyCriteria.studyCriteriaUid, data)
      bus.$emit('notification', { msg: this.$t('EligibilityCriteriaEditForm.update_success') })
      this.$emit('updated')
      this.close()
    }
  },
  mounted () {
    this.loadTemplateParameters()
  },
  watch: {
    studyCriteria (value) {
      if (value) {
        this.loadTemplateParameters()
      }
    },
    parameters () {
      this.parameters.forEach(el => {
        if (el.name === 'TextValue' && el.selectedValues && el.selectedValues.length) {
          this.parameters[this.parameters.indexOf(el)].selectedValues = el.selectedValues[0].name
        }
      })
    }
  }
}
</script>
