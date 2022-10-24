<template>
<simple-form-dialog
  ref="form"
  :title="title"
  :help-items="helpItems"
  @close="close"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <validation-provider
        v-if="!timeframe"
        v-slot="{ errors }"
        name="Library"
        rules="required"
        >
        <v-row>
          <v-col>
            <v-select
              v-model="form.library"
              :label="$t('_global.library')"
              :items="libraries"
              item-text="name"
              return-object
              :error-messages="errors"
              dense
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-if="!timeframe || timeframe.uid === undefined"
          v-slot="{ errors }"
          name="Template"
          rules="required"
        >
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.timeframeTemplate"
              :label="$t('TimeframeForm.select_template')"
              :items="templates"
              item-text="name"
              return-object
              single-line
              :error-messages="errors"
              @change="showParametersFromTemplate"
              dense
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <div v-if="timeframeName">
        <v-row dense>
          <v-col cols="12">
            <small>{{ $t('TimeframeForm.current_timeframe') }}</small>
          </v-col>
        </v-row>
        <v-row dense class="pb-2">
          <v-col cols="12">
            <n-n-parameter-highlighter
              :name="timeframeName"
              :show-prefix-and-postfix="false"
              ></n-n-parameter-highlighter>
          </v-col>
        </v-row>
      </div>
      <div v-if="timeframeTemplateName">
        <v-row dense class="pb-2">
          <v-col cols="12">
            <parameter-value-selector
              :value="parameters"
              :template="timeframeTemplateName"
              />
          </v-col>
        </v-row>
      </div>
      <v-row v-if="timeframe">
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            name="ChangeDescription"
            rules="required"
            >
            <v-row>
              <v-col>
                <v-textarea
                  :label="$t('HistoryTable.change_description')"
                  v-model="form.changeDescription"
                  :error-messages="errors"
                  rows="1"
                  color="white"
                  auto-grow
                  ></v-textarea>
              </v-col>
            </v-row>
          </validation-provider>
        </v-col>
      </v-row>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>
import libraries from '@/api/libraries'
import timeframeTemplates from '@/api/timeframeTemplates'
import timeframes from '@/api/timeframes'
import statuses from '@/constants/statuses'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector'
import { objectManagerMixin } from '@/mixins/objectManager'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'

export default {
  mixins: [objectManagerMixin],
  components: {
    NNParameterHighlighter,
    ParameterValueSelector,
    SimpleFormDialog
  },
  props: {
    timeframe: Object,
    open: Boolean
  },
  computed: {
    title () {
      return (this.timeframe)
        ? this.$t('TimeframeForm.edit_title')
        : this.$t('TimeframeForm.add_title')
    },
    isParameterTemplate () {
      let isTemplate = false
      this.parameterResponse.forEach(value => {
        if (value.format) {
          isTemplate = true
        }
      })
      return isTemplate
    },
    timeframeTemplateName () {
      const timeframeTemplate = this.timeframe ? this.timeframe.timeframeTemplate : this.form.timeframeTemplate
      if (timeframeTemplate) {
        if (this.isParameterTemplate) {
          return this.calculateTemplateName
        } else {
          return timeframeTemplate.name
        }
      }
      return ''
    },
    calculateTemplateName () {
      const timeframeTemplate = this.timeframe ? this.timeframe.timeframeTemplate : this.form.timeframeTemplate
      let result = timeframeTemplate.name
      this.parameterResponse.forEach(value => {
        if (value.format) {
          result = result.replace('[' + value.name + ']', value.format)
        }
      })
      return result
    },
    timeframeName () {
      return this.timeframe ? this.timeframe.name : ''
    },
    objectUid () {
      return this.timeframe.uid
    },
    /*
    ** Compute timeframe's name based on selected parameters.
    */
    timeframeNamePreview () {
      if (!this.timeframeTemplateName || !this.parameters.length) {
        return ''
      }
      return this.getNamePreview(this.timeframeTemplateName, this.parameters)
    }
  },
  data () {
    return {
      form: this.getInitialFormContent(),
      helpItems: [
        'TimeframeForm.select_template'
      ],
      parameterResponse: [],
      libraries: [],
      parameters: [],
      templates: [],
      apiEndpoint: timeframes,
      apiTemplateEndpoint: timeframeTemplates,
      storeEndpointAdd: 'timeframes/addTimeframe',
      storeEndpointUpdate: 'timeframes/updateTimeframe',
      translationLabel: 'TimeframeForm',
      objectTemplateUidLabel: 'timeframeTemplateUid',
      objectTemplateUidResultLabel: 'timeframeTemplate'
    }
  },
  methods: {
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.$refs.form.working = true
      try {
        if (!this.timeframe) {
          await this.addObject()
        } else {
          await this.updateObject()
        }
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    }
  },
  mounted () {
    libraries.get(1).then(resp => {
      this.libraries = resp.data
    })
    timeframeTemplates.get({ status: statuses.FINAL }).then(resp => {
      this.templates = resp.data
    })
    if (this.timeframe) {
      this.showParametersFromObject(this.timeframe)
    }
  },
  watch: {
    timeframe (value) {
      if (value) {
        this.showParametersFromObject(value)
      }
    }
  }
}
</script>
