<template>
<v-card color="dfltBackground">
  <v-card-title>
    <span class="dialog-title">{{ getTitle() }}</span>
    <help-button-with-panels :title="$t('_global.help')" :items="helpItems" />
  </v-card-title>
  <v-card-text class="mt-4">
    <validation-observer ref="observer">
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            name="Name"
            vid="name"
            rules="required"
            >
            <div class="pa-6 white">
              <n-n-template-input-field
                v-model="form.name"
                :items="parameterTypes"
                :error-messages="errors"
                :show-drop-down-early="true"
                :label="$t(translationObject + '.name')"
                ></n-n-template-input-field>
            </div>
          </validation-provider>
        </v-col>
      </v-row>
      <slot name="extraFields" :form="form"></slot>
      <v-row v-if="template">
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            name="ChangeDescription"
            rules="required"
            >
            <v-textarea
              v-model="form.changeDescription"
              :label="$t('HistoryTable.change_description')"
              :error-messages="errors"
              rows="1"
              dense
              clearable
              auto-grow
              class="white pa-5"
              ></v-textarea>
          </validation-provider>
        </v-col>
      </v-row>

      <v-expansion-panels flat class="mt-6" v-if="withClassificationAttributes" v-model="panel">
        <v-expansion-panel>
          <v-expansion-panel-header>
            {{ $t('GenericTemplateForm.template_properties') }}
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <not-applicable-field
              :clean-function="updateIndicationsNA"
              :checked="template && !template.indications"
              >
              <template v-slot:mainField="{ notApplicable }">
                <validation-provider
                  v-slot="{ errors }"
                  name="ChangeDescription"
                  :rules="`requiredIfNotNA:${notApplicable}`"
                  >
                  <multiple-select
                    v-model="form.indications"
                    :label="$t('GenericTemplateForm.study_indication')"
                    :items="indications"
                    return-object
                    item-text="name"
                    item-value="termUid"
                    :disabled="notApplicable"
                    :errors="errors"
                    />
                </validation-provider>
              </template>
            </not-applicable-field>
            <slot name="templateFields" v-bind:form="form"></slot>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
    </validation-observer>
  </v-card-text>
  <v-card-actions class="pb-6 px-6">
    <v-spacer></v-spacer>
    <v-btn
      class="secondary-btn"
      color="white"
      @click="cancel"
      >
      {{ $t('_global.cancel') }}
    </v-btn>
    <v-btn
      class="secondary-btn"
      color="white"
      @click="verifySyntax"
      >
      {{ $t('_global.verify_syntax') }}
    </v-btn>
    <v-btn
      color="secondary"
      @click="submit"
      :loading="loading"
      >
      {{ $t('_global.save') }}
    </v-btn>
  </v-card-actions>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</v-card>
</template>

<script>
import _isEqual from 'lodash/isEqual'
import { bus } from '@/main'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import dictionaries from '@/api/dictionaries'
import libraries from '@/api/libraries'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'
import MultipleSelect from '@/components/tools/MultipleSelect'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField'
import NotApplicableField from '@/components/tools/NotApplicableField'
import statuses from '@/constants/statuses'
import templatesApi from '@/api/templates'
import templateParameterTypes from '@/api/templateParameterTypes'

export default {
  props: {
    template: Object,
    urlPrefix: {
      type: String,
      default: ''
    },
    translationType: {
      type: String,
      default: ''
    },
    objectType: {
      type: String,
      default: ''
    },
    withClassificationAttributes: {
      type: Boolean,
      default: true
    },
    openClassificationAttributes: {
      type: Boolean,
      default: false
    },
    loadFormFunction: {
      type: Function,
      required: false
    },
    preparePayloadFunction: {
      type: Function,
      required: false
    },
    getHelpFunction: Function,
    title: {
      type: String,
      required: false
    },
    typeUid: String
  },
  components: {
    HelpButtonWithPanels,
    MultipleSelect,
    NNTemplateInputField,
    NotApplicableField,
    ConfirmDialog
  },
  data () {
    return {
      api: null,
      form: this.getInitialFormContent(),
      libraries: [],
      loading: false,
      panel: null,
      parameterTypes: [],
      indications: []
    }
  },
  created () {
    this.api = templatesApi(this.urlPrefix)
    libraries.get(1).then(resp => {
      this.libraries = resp.data
    })
    this.loadParameterTypes()
    if (this.openClassificationAttributes) {
      this.panel = 0
    }
  },
  computed: {
    translationObject () {
      return this.translationType.replace('Table', 'Form')
    },
    helpItems () {
      const items = [
        `${this.translationObject}.name`,
        'GenericTemplateForm.study_indication'
      ]
      if (this.getHelpFunction) {
        return items.concat(this.getHelpFunction())
      }
      return items
    }
  },
  methods: {
    getInitialFormContent () {
      return {
        library: {
          name: 'Sponsor'
        }
      }
    },
    getTitle () {
      if (this.title) {
        return this.title
      }
      return (this.template)
        ? this.$t(this.translationObject + '.edit_title')
        : this.$t(this.translationObject + '.add_title')
    },
    loadParameterTypes () {
      templateParameterTypes.getTypes().then(resp => {
        this.parameterTypes = resp.data
      })
    },
    addTemplate () {
      const data = { ...this.form }
      data.typeUid = this.typeUid
      if (data.indications && data.indications.length > 0) {
        if (this.template !== null && _isEqual(data.indications, this.template.indications)) {
          data.indicationUids = data.indications.map(item => item.termUid)
        } else {
          data.indicationUids = data.indications.map(item => item.termUid)
        }
      }
      if (this.preparePayloadFunction) {
        this.preparePayloadFunction(data)
      }
      return this.api.create(data).then(resp => {
        this.$emit('templateAdded')
        bus.$emit('notification', { msg: this.$t(this.translationObject + '.add_success') })
        this.close()
      })
    },
    updateIndicationsNA (value) {
      if (value) {
        this.$set(this.form, 'indications', null)
      }
    },
    injectParameter (parameter) {
      if (this.form.name === undefined) {
        this.$set(this.form, 'name', '')
      }
      this.$set(this.form, 'name', this.form.name + ` [${parameter.name}]`)
    },
    updateTemplate () {
      const data = { ...this.form }
      if (data.indications && data.indications.length > 0) {
        data.indicationUids = data.indications.map(item => item.termUid)
        delete data.indications
      }
      if (this.preparePayloadFunction) {
        this.preparePayloadFunction(data)
      }
      return this.api.update(this.template.uid, data).then(resp => {
        this.$emit('templateUpdated', resp.data)
        bus.$emit('notification', { msg: this.$t(this.translationObject + '.update_success') })
        this.close()
      })
    },
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.loading = true
      try {
        if (!this.template) {
          await this.addTemplate()
        } else {
          await this.updateTemplate()
        }
      } catch (error) {
        if (error.response.status === 403) {
          this.$refs.observer.setErrors({ name: [error.response.data.message] })
        }
      } finally {
        this.loading = false
      }
    },
    async cancel () {
      if (this.$store.getters['form/form'] === '' || _isEqual(this.$store.getters['form/form'], JSON.stringify(this.form))) {
        this.close()
      } else {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue')
        }
        if (await this.$refs.confirm.open(this.$t('_global.cancel_changes'), options)) {
          this.close()
        }
      }
    },
    close () {
      this.form = this.getInitialFormContent()
      this.$store.commit('form/CLEAR_FORM')
      this.$refs.observer.reset()
      this.$emit('close')
    },
    verifySyntax () {
      if (!this.form.name) {
        return
      }
      const data = { name: this.form.name }
      this.api.preValidate(data).then(resp => {
        bus.$emit(
          'notification',
          { msg: this.$t('_global.valid_syntax') })
      })
    },
    /**
     * Do a step by step loading of the form using the given template because we don't want to include every fields.
     */
    loadFormFromTemplate () {
      this.form = {
        name: this.template ? this.template.name : null,
        library: this.template ? this.template.library : { name: 'Sponsor' },
        indications: this.template ? this.template.indications : null
      }
      if (this.template.status === statuses.DRAFT) {
        this.$set(this.form, 'changeDescription', this.$t('_global.work_in_progress'))
      }
      if (this.loadFormFunction) {
        this.loadFormFunction(this.form)
      } else {
        this.$store.commit('form/SET_FORM', this.form)
      }
    }
  },
  mounted () {
    if (this.template) {
      this.loadFormFromTemplate()
    }
    dictionaries.getCodelists('SNOMED').then(resp => {
      /* FIXME: we need a direct way to retrieve the terms here */
      dictionaries.getTerms({ codelist_uid: resp.data.items[0].codelistUid }).then(resp => {
        this.indications = resp.data.items
      })
    })
  },
  watch: {
    template (value) {
      if (value) {
        this.loadFormFromTemplate()
      }
    }
  }
}
</script>

<style scoped>
.v-expansion-panel-header {
  font-size: 1.1rem !important;
}
</style>
