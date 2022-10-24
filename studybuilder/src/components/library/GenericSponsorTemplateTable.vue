<template>
<div>
  <n-n-table
    v-model="selected"
    :headers="headers"
    :items="expandedTemplates"
    item-key="uid"
    :export-object-label="objectType"
    :export-data-url="urlPrefix"
    :server-items-length="total"
    sort-by="startDate"
    sort-desc
    :options.sync="options"
    :has-api="hasApi"
    :column-data-resource="urlPrefix"
    @filter="filter"
    has-history
    >
    <template v-slot:actions="">
      <v-btn
        fab
        dark
        small
        color="primary"
        @click="createTemplate()"
        :title="$t(`${translationType}.add`)"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-for="(_, slot) of $scopedSlots" v-slot:[slot]="scope">
      <slot :name="slot" v-bind="scope" />
    </template>
    <template v-slot:item.indications.name="{ item }">
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
    <template v-slot:item.startDate="{ item }">
      <template v-if="item.defaultParameterValuesSet === undefined">
        {{ item.startDate | date }}
      </template>
    </template>
    <template v-slot:item.status="{ item }">
      <template v-if="item.defaultParameterValuesSet === undefined">
        <status-chip :status="item.status" />
      </template>
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu
        v-if="item.defaultParameterValuesSet === undefined"
        :actions="actions"
        :item="item"
        />
      <actions-menu
        v-else
        :actions="fakeTemplateActions"
        :item="item"
        />
    </template>
  </n-n-table>
  <v-dialog v-model="showForm"
            persistent
            :fullscreen="fullscreenForm"
            :max-width="fullscreenForm ? null : '800px'"
            :content-class="fullscreenForm ? 'fullscreen-dialog' : 'top-dialog'"
            :key="key"
            >
    <slot
      name="editform"
      v-bind:closeForm="closeForm"
      v-bind:selectedObject="selectedObject"
      v-bind:filter="filter"
      v-bind:updateTemplate="updateTemplate"
      >
    </slot>
  </v-dialog>
  <v-dialog v-model="showOTHistory"
            persistent
            max-width="1200px">
    <history-table @close="closeHistory" :type="objectType" :url-prefix="urlPrefix+'/'"
                   :item="selectedObject" :title-label="appLabel" />
  </v-dialog>
  <default-parameter-values-set-form
    :open="showParameterValuesSetForm"
    :set-number="currentParameterValuesSetNumber"
    :values-set="currentParameterValuesSet"
    :template="currentParameterValuesSetTemplate"
    :object-type="getBaseObjectType()"
    @close="closeDefaultParameterValuesSetForm"
    />
  <confirm-dialog ref="confirm" :action-cols="5" :text-cols="6" />
  <v-dialog v-model="showIndexingForm"
            persistent
            max-width="800px"
            >
    <slot name="indexingDialog"
          v-bind:closeDialog="() => showIndexingForm = false"
          v-bind:template="selectedObject"
          v-bind:show="showIndexingForm"
          />
  </v-dialog>
</div>
</template>

<script>
import Vue from 'vue'
import { bus } from '@/main'
import templates from '@/api/templates'
import ActionsMenu from '@/components/tools/ActionsMenu'
import defaultParameterValues from '@/utils/defaultParameterValues'
import DefaultParameterValuesSetForm from '@/components/library/DefaultParameterValuesSetForm'
import HistoryTable from '@/components/library/HistoryTable'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import StatusChip from '@/components/tools/StatusChip'
import statuses from '@/constants/statuses'
import filteringParameters from '@/utils/filteringParameters'

export default Vue.extend({
  name: 'studybuilder-template-table',
  props: {
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
    hasApi: {
      type: Boolean,
      default: false
    },
    columnDataResource: {
      type: String,
      default: ''
    },
    headers: {
      type: Array,
      default: function () {
        return [
          {
            text: '',
            value: 'actions',
            sortable: false,
            width: '5%'
          },
          { text: this.$t('_global.library'), value: 'library.name' },
          { text: this.$t('_global.template'), value: 'name', width: '30%' },
          { text: this.$t('_global.modified'), value: 'startDate' },
          { text: this.$t('_global.modified_by'), value: 'fixme' },
          { text: this.$t('_global.status'), value: 'status' },
          { text: this.$t('_global.version'), value: 'version' }
        ]
      }
    },
    extraFiltersFunc: {
      type: Function,
      required: false
    },
    fullscreenForm: {
      type: Boolean,
      default: false
    },
    withIndexingProperties: {
      type: Boolean,
      default: true
    }
  },
  components: {
    ActionsMenu,
    DefaultParameterValuesSetForm,
    HistoryTable,
    NNParameterHighlighter,
    ConfirmDialog,
    NNTable,
    StatusChip
  },
  data () {
    const actions = [
      {
        label: this.$t('_global.add_defaults'),
        icon: 'mdi-plus-circle',
        iconColor: 'primary',
        click: this.addDefaultParameterValuesSet
      },
      {
        label: this.$t('_global.edit'),
        icon: 'mdi-pencil',
        iconColor: 'primary',
        condition: (item) => item.possibleActions.find(action => action === 'edit'),
        click: this.editTemplate
      },
      {
        label: this.$t('_global.approve'),
        icon: 'mdi-check-decagram',
        iconColor: 'success',
        condition: (item) => item.possibleActions.find(action => action === 'approve'),
        click: this.approveTemplate
      },
      {
        label: this.$t('_global.new_version'),
        icon: 'mdi-plus-circle-outline',
        iconColor: 'primary',
        condition: (item) => item.possibleActions.find(action => action === 'newVersion'),
        click: this.createNewVersion
      },
      {
        label: this.$t('_global.inactivate'),
        icon: 'mdi-close-octagon-outline',
        iconColor: 'primary',
        condition: (item) => item.possibleActions.find(action => action === 'inactivate'),
        click: this.inactivateTemplate
      },
      {
        label: this.$t('_global.reactivate'),
        icon: 'mdi-undo-variant',
        iconColor: 'primary',
        condition: (item) => item.possibleActions.find(action => action === 'reactivate'),
        click: this.reactivateTemplate
      },
      {
        label: this.$t('_global.delete'),
        icon: 'mdi-delete',
        iconColor: 'error',
        condition: (item) => item.possibleActions.find(action => action === 'delete'),
        click: this.deleteTemplate
      },
      {
        label: this.$t('_global.history'),
        icon: 'mdi-history',
        click: this.openTemplateHistory
      }
    ]
    if (this.withIndexingProperties) {
      actions.unshift({
        label: this.$t('_global.edit_indexing'),
        icon: 'mdi-pencil',
        iconColor: 'primary',
        condition: (item) => item.status === statuses.FINAL,
        click: this.editTemplateIndexing
      })
    }
    return {
      actions,
      currentParameterValuesSet: null,
      currentParameterValuesSetNumber: null,
      currentParameterValuesSetTemplate: null,
      fakeTemplateActions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editDefaultParameterValuesSet
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteDefaultParameterValuesSet
        }
      ],
      api: null,
      showForm: false,
      showIndexingForm: false,
      showOTHistory: false,
      showParameterValuesSetForm: false,
      selectedObject: null,
      appLabel: this.$t(this.translationType + '.singular_title'),
      selected: [],
      templates: [],
      options: {},
      total: 0,
      key: 0
    }
  },
  computed: {
    expandedTemplates () {
      const result = []
      for (const template of this.templates) {
        result.push(template)
        if (defaultParameterValues.hasDefaultParameterValues(template)) {
          for (const setNumber in template.defaultParameterValues) {
            const fakeTemplate = {
              baseTemplate: template,
              name: template.name,
              defaultParameterValuesSet: setNumber
            }
            fakeTemplate.defaultParameterValues = template.defaultParameterValues[setNumber]
            result.push(fakeTemplate)
          }
        }
      }
      return result
    }
  },
  created () {
    this.api = templates(this.urlPrefix)
  },
  methods: {
    createTemplate () {
      this.selectedObject = null
      this.showForm = true
    },
    editTemplate (template) {
      this.selectedObject = template
      this.showForm = true
    },
    updateTemplate (template, status) {
      this.templates.filter((item, pos) => {
        if (item.uid === template.uid && item.status === status) {
          this.$set(this.templates, pos, template)
        }
      })
    },
    async approveTemplate (template) {
      if (template.uid.includes('ActivityDescriptionTemplate')) { // Temporary workaround for Activity Templates, will be deleted after backend instantiations activities implement
        this.api.approveCascade(template.uid, false).then(resp => {
          this.updateTemplate(resp.data, template.status)
          bus.$emit('notification', { msg: this.$t(this.translationType + '.approve_success') })
        })
      } else {
        this.api.approveCascade(template.uid, true).then(resp => {
          this.updateTemplate(resp.data, template.status)
          bus.$emit('notification', { msg: this.$t(this.translationType + '.approve_success') })
        })
      }
    },
    inactivateTemplate (template) {
      this.api.inactivate(template.uid).then(resp => {
        this.updateTemplate(resp.data, template.status)
        bus.$emit('notification', { msg: this.$t(this.translationType + '.inactivate_success') })
      })
    },
    reactivateTemplate (template) {
      this.api.reactivate(template.uid).then(resp => {
        this.updateTemplate(resp.data, template.status)
        bus.$emit('notification', { msg: this.$t(this.translationType + '.reactivate_success') })
      })
    },
    deleteTemplate (template) {
      this.api.delete(template.uid).then(resp => {
        this.filter()
        bus.$emit('notification', { msg: this.$t(this.translationType + '.delete_success') })
      })
    },
    editTemplateIndexing (template) {
      this.selectedObject = template
      this.showIndexingForm = true
    },
    openTemplateHistory (template) {
      this.selectedObject = template
      this.showOTHistory = true
    },
    async createNewVersion (template) {
      if (template.studyCount > 0) {
        const options = {
          cancelLabel: this.$t('_global.cancel_cascade_update'),
          agreeLabel: this.$t('_global.create_new_version'),
          type: 'warning',
          width: 1000
        }
        if (!await this.$refs.confirm.open(this.$tc('_global.cascade_update_warning', template.studyCount, { count: template.studyCount }), options)) {
          return
        }
      }
      const data = {
        name: template.name,
        changeDescription: this.$t(this.translationType + '.new_version_default_description')
      }
      this.api.createNewVersion(template.uid, data).then(resp => {
        this.updateTemplate(resp.data, template.status)
        bus.$emit('notification', { msg: this.$t(this.translationType + '.new_version_success') })
      })
    },
    closeForm () {
      this.selectedObject = null
      this.showForm = false
      this.key += 1
    },
    closeHistory () {
      this.selectedObject = null
      this.showOTHistory = false
    },
    filter (filters, sort, filtersUpdated) {
      filters = (filters) ? JSON.parse(filters) : {}
      filters['library.name'] = { v: ['Sponsor'] }
      if (this.extraFiltersFunc) {
        this.extraFiltersFunc(filters)
      }
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      this.api.get(params).then(resp => {
        if (resp.data.items !== undefined) {
          this.templates = resp.data.items
          this.total = resp.data.total
        } else {
          this.templates = resp.data
          this.total = this.templates.length
        }
      })
    },
    addDefaultParameterValuesSet (template) {
      this.currentParameterValuesSetTemplate = template
      this.currentParameterValuesSet = []
      this.showParameterValuesSetForm = true
    },
    editDefaultParameterValuesSet (item) {
      this.currentParameterValuesSetNumber = item.defaultParameterValuesSet
      this.currentParameterValuesSet = item.defaultParameterValues
      this.currentParameterValuesSetTemplate = item.baseTemplate
      this.showParameterValuesSetForm = true
    },
    async deleteDefaultParameterValuesSet (item) {
      const options = {
        type: 'warning'
      }
      if (!await this.$refs.confirm.open(this.$t('GenericTemplateTable.confirm_parameter_values_delete'), options)) {
        return
      }
      await this.api.deleteDefaultParameterValuesSet(item.baseTemplate.uid, item.defaultParameterValuesSet)
      this.filter()
    },
    closeDefaultParameterValuesSetForm () {
      this.showParameterValuesSetForm = false
      this.currentParameterValuesSetNumber = null
      this.currentParameterValuesSet = null
      this.filter()
    },
    getBaseObjectType () {
      let result = this.objectType.replace('Templates', '')
      if (result === 'activity') {
        result = 'activity-description'
      }
      return result
    }
  },
  watch: {
    options: {
      handler () {
        this.filter()
      },
      deep: true
    }
  }
})
</script>
