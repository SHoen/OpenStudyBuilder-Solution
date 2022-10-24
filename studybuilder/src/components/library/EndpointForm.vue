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
        v-if="!endpoint"
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
              ></v-select>
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-if="!endpoint || endpoint.uid === undefined"
        v-slot="{ errors }"
        name="Template"
        rules="required"
        >
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.endpointTemplate"
              :label="$t('EndpointForm.select_template')"
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
      <div v-if="endpointName">
        <v-row dense>
          <v-col cols="12">
            <small>{{ $t('EndpointForm.current_endpoint') }}</small>
          </v-col>
        </v-row>
        <v-row dense class="pb-2">
          <v-col cols="12">
            <n-n-parameter-highlighter
              :name="endpointName"
              :show-prefix-and-postfix="false"
              ></n-n-parameter-highlighter>
          </v-col>
        </v-row>
      </div>
      <div v-if="endpointTemplateName">
        <v-row dense class="pb-2">
          <v-col cols="12">
            <parameter-value-selector
              :value="parameters"
              :template="endpointTemplateName"
              />
          </v-col>
        </v-row>
      </div>
      <v-row v-if="endpoint">
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
                  :rows="1"
                  class="white"
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
import endpointTemplates from '@/api/endpointTemplates'
import endpoints from '@/api/endpoints'
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
    endpoint: Object,
    open: Boolean
  },
  computed: {
    title () {
      return (this.endpoint)
        ? this.$t('EndpointForm.edit_title')
        : this.$t('EndpointForm.add_title')
    },
    endpointTemplateName () {
      const endpointTemplate = this.endpoint ? this.endpoint.endpointTemplate : this.form.endpointTemplate
      if (endpointTemplate) {
        return endpointTemplate.name
      }
      return ''
    },
    endpointName () {
      return this.endpoint ? this.endpoint.name : ''
    },
    objectUid () {
      return this.endpoint.uid
    },
    /*
    ** Compute endpoint's name based on selected parameters.
    */
    endpointNamePreview () {
      if (!this.endpointTemplateName || !this.parameters.length) {
        return ''
      }
      return this.getNamePreview(this.endpointTemplateName, this.parameters)
    }
  },
  data () {
    return {
      form: this.getInitialFormContent(),
      helpItems: [
        'EndpointForm.select_template'
      ],
      libraries: [],
      parameters: [],
      templates: [],
      apiEndpoint: endpoints,
      apiTemplateEndpoint: endpointTemplates,
      storeEndpointAdd: 'endpoints/addEndpoint',
      storeEndpointUpdate: 'endpoints/updateEndpoint',
      translationLabel: 'EndpointForm',
      objectTemplateUidLabel: 'endpointTemplateUid',
      objectTemplateUidResultLabel: 'endpointTemplate'
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
        if (!this.endpoint) {
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
    endpointTemplates.get({ status: statuses.FINAL }).then(resp => {
      this.templates = resp.data.items
    })
    if (this.endpoint) {
      this.showParametersFromObject(this.endpoint)
    }
  },
  watch: {
    endpoint (value) {
      if (value) {
        this.showParametersFromObject(value)
      }
    }
  }
}
</script>
