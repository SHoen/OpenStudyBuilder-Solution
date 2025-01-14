<template>
<div>
  <n-n-table
    :headers="headers"
    :items="templates"
    item-key="uid"
    sort-by="name"
    sort-desc
    has-api
    :options.sync="options"
    :server-items-length="total"
    @filter="getTemplates"
    column-data-resource="concepts/odms/study-events"
    export-data-url="concepts/odms/study-events"
    export-object-label="CRFTemplates"
    >
    <template v-slot:actions="">
      <v-btn
        class="ml-2"
        fab
        small
        color="primary"
        @click.stop="openForm()"
        :title="$t('CrfTemplates.add_template')"
        data-cy="add-crf-template"
        :disabled="!checkPermission($roles.LIBRARY_WRITE)"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
    <template v-slot:item.status="{ item }">
      <status-chip :status="item.status" />
    </template>
    <template v-slot:item.relations="{ item }">
      <v-btn
        fab
        dark
        small
        color="primary"
        icon
        @click="openRelationsTree(item)"
        >
        <v-icon dark>
          mdi-family-tree
        </v-icon>
      </v-btn>
    </template>
  </n-n-table>
  <crf-template-form
    :open="showForm"
    @close="closeForm"
    :selectedTemplate="selectedTemplate"
    :readOnlyProp="selectedTemplate && selectedTemplate.status === statuses.FINAL"
    />
  <v-dialog
    v-model="showTemplateHistory"
    @keydown.esc="closeTemplateHistory"
    persistent
    :max-width="globalHistoryDialogMaxWidth"
    :fullscreen="globalHistoryDialogFullscreen"
    >
    <history-table
      :title="templateHistoryTitle"
      @close="closeTemplateHistory"
      :headers="headers"
      :items="templateHistoryItems"
      />
  </v-dialog>
  <v-dialog v-model="showRelations"
            @keydown.esc="closeRelationsTree()"
            max-width="800px"
            persistent>
    <odm-references-tree
      :item="selectedTemplate"
      type="template"
      @close="closeRelationsTree()"/>
  </v-dialog>
</div>
</template>

<script>
import NNTable from '@/components/tools/NNTable'
import ActionsMenu from '@/components/tools/ActionsMenu'
import crfs from '@/api/crfs'
import HistoryTable from '@/components/tools/HistoryTable'
import CrfTemplateForm from '@/components/library/crfs/CrfTemplateForm'
import StatusChip from '@/components/tools/StatusChip'
import filteringParameters from '@/utils/filteringParameters'
import OdmReferencesTree from '@/components/library/crfs/OdmReferencesTree'
import crfTypes from '@/constants/crfTypes'
import { mapGetters } from 'vuex'
import statuses from '@/constants/statuses'
import { accessGuard } from '@/mixins/accessRoleVerifier'

export default {
  mixins: [accessGuard],
  components: {
    NNTable,
    ActionsMenu,
    HistoryTable,
    CrfTemplateForm,
    StatusChip,
    OdmReferencesTree
  },
  props: {
    elementProp: Object
  },
  computed: {
    ...mapGetters({
      templates: 'crfs/templates',
      total: 'crfs/totalTemplates'
    }),
    templateHistoryTitle () {
      if (this.selectedTemplate) {
        return this.$t(
          'CrfTemplates.template_history_title',
          { templateUid: this.selectedTemplate.uid })
      }
      return ''
    }
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) => item.possible_actions.find(action => action === 'approve'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.approveTemplate
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) => item.possible_actions.find(action => action === 'edit'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.edit
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: (item) => item.possible_actions.find(action => action === 'delete'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.deleteTemplate
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) => item.possible_actions.find(action => action === 'new_version'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.newTemplateVersion
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) => item.possible_actions.find(action => action === 'inactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.inactivateTemplate
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) => item.possible_actions.find(action => action === 'reactivate'),
          accessRole: this.$roles.LIBRARY_WRITE,
          click: this.reactivateTemplate
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openTemplateHistory
        }
      ],
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('CrfTemplates.oid'), value: 'oid' },
        { text: this.$t('_global.relations'), value: 'relations' },
        { text: this.$t('_global.name'), value: 'name' },
        { text: this.$t('CrfTemplates.effective_date'), value: 'effective_date' },
        { text: this.$t('CrfTemplates.retired_date'), value: 'retired_date' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.status'), value: 'status' }
      ],
      showForm: false,
      showTemplateHistory: false,
      selectedTemplate: null,
      options: {},
      filters: '',
      showRelations: false,
      templateHistoryItems: []
    }
  },
  created () {
    this.statuses = statuses
  },
  mounted () {
    this.getTemplates()
    if (this.elementProp.tab === 'templates' && this.elementProp.type === crfTypes.TEMPLATE && this.elementProp.uid) {
      crfs.getTemplate(this.elementProp.uid).then((resp) => {
        this.edit(resp.data)
      })
    }
  },
  methods: {
    openRelationsTree (item) {
      this.showRelations = true
      this.selectedTemplate = item
    },
    closeRelationsTree () {
      this.selectedTemplate = null
      this.showRelations = false
    },
    approveTemplate (item) {
      crfs.approve('study-events', item.uid).then((resp) => {
        this.getTemplates()
      })
    },
    inactivateTemplate (item) {
      crfs.inactivate('study-events', item.uid).then((resp) => {
        this.getTemplates()
      })
    },
    reactivateTemplate (item) {
      crfs.reactivate('study-events', item.uid).then((resp) => {
        this.getTemplates()
      })
    },
    newTemplateVersion (item) {
      crfs.newVersion('study-events', item.uid).then((resp) => {
        this.getTemplates()
      })
    },
    deleteTemplate (item) {
      crfs.delete('study-events', item.uid).then((resp) => {
        this.getTemplates()
      })
    },
    edit (item) {
      crfs.getTemplate(item.uid).then((resp) => {
        this.selectedTemplate = resp.data
        this.showForm = true
        this.$emit('clearUid')
      })
    },
    async openTemplateHistory (template) {
      this.selectedTemplate = template
      const resp = await crfs.getTemplateAuditTrail(template.uid)
      this.templateHistoryItems = resp.data
      this.showTemplateHistory = true
    },
    closeTemplateHistory () {
      this.showTemplateHistory = false
      this.selectedTemplate = null
    },
    openForm () {
      this.selectedTemplate = null
      this.showForm = true
    },
    closeForm () {
      this.selectedTemplate = null
      this.showForm = false
      this.getTemplates()
    },
    getTemplates (filters, sort, filtersUpdated) {
      if (filters) {
        this.filters = filters
      }
      const params = filteringParameters.prepareParameters(
        this.options, this.filters, sort, filtersUpdated)
      this.$store.dispatch('crfs/fetchTemplates', params)
    }
  },
  watch: {
    options: {
      handler () {
        this.getTemplates()
      },
      deep: true
    },
    elementProp (value) {
      if (value.tab === 'templates' && value.type === crfTypes.TEMPLATE && value.uid) {
        this.edit({ uid: value.uid })
      }
    }
  }
}
</script>
