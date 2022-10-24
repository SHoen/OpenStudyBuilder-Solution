<template>
<div>
  <n-n-table
    :headers="headers"
    :items="templates"
    item-key="uid"
    sort-by="name"
    sort-desc
    has-api
    column-data-resource="concepts/odms/templates"
    export-data-url="concepts/odms/templates"
    :options.sync="options"
    :server-items-length="total"
    @filter="getTemplates"
    has-history
    >
    <template v-slot:actions="">
      <v-btn
        class="ml-2"
        fab
        dark
        small
        color="primary"
        @click.stop="openForm()"
        :title="$t('CrfTemplates.add_template')"
        data-cy="add-crf-template"
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
    />
  <v-dialog v-model="showTemplateHistory"
            persistent
            max-width="1200px">
    <history-table @close="closeTemplateHistory" type="crfTemplate" :item="templateHistory"
                   :title-label="$t('CrfTemplates.crf_template')" />
  </v-dialog>
  <v-dialog v-model="showRelations"
            max-width="800px"
            persistent>
    <odm-references-tree
      :item="selectedTemplate"
      type="template"
      @close="closeRelationsTree()"/>
  </v-dialog>
  <v-dialog v-model="showDuplicationForm"
            persistent>
    <crf-duplication-form
      @close="closeDuplicateForm"
      :item="selectedTemplate"
      type="template"
      />
  </v-dialog>
</div>
</template>

<script>
import NNTable from '@/components/tools/NNTable'
import ActionsMenu from '@/components/tools/ActionsMenu'
import crfs from '@/api/crfs'
import HistoryTable from '@/components/library/HistoryTable'
import CrfTemplateForm from '@/components/library/CrfTemplateForm'
import StatusChip from '@/components/tools/StatusChip'
import filteringParameters from '@/utils/filteringParameters'
import OdmReferencesTree from '@/components/library/OdmReferencesTree.vue'
import CrfDuplicationForm from '@/components/library/CrfDuplicationForm'

export default {
  components: {
    NNTable,
    ActionsMenu,
    HistoryTable,
    CrfTemplateForm,
    StatusChip,
    OdmReferencesTree,
    CrfDuplicationForm
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) => item.possibleActions.find(action => action === 'approve'),
          click: this.approveTemplate
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'edit'),
          click: this.editTemplate
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => item.possibleActions.find(action => action === 'delete'),
          click: this.deleteTemplate
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'newVersion'),
          click: this.newTemplateVersion
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
          label: this.$t('_global.duplicate'),
          icon: 'mdi-content-copy',
          iconColor: 'primary',
          click: this.openDuplicateForm
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
        { text: this.$t('CrfTemplates.effective_date'), value: 'effectiveDate' },
        { text: this.$t('CrfTemplates.retired_date'), value: 'retiredDate' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.status'), value: 'status' }
      ],
      showForm: false,
      showTemplateHistory: false,
      selectedTemplate: null,
      templateHistory: null,
      options: {},
      filters: '',
      total: 0,
      templates: [],
      showRelations: false,
      showDuplicationForm: false
    }
  },
  methods: {
    openDuplicateForm (item) {
      this.selectedTemplate = item
      this.showDuplicationForm = true
    },
    closeDuplicateForm () {
      this.showDuplicationForm = false
      this.getTemplates()
    },
    openRelationsTree (item) {
      this.showRelations = true
      this.selectedTemplate = item
    },
    closeRelationsTree () {
      this.selectedTemplate = null
      this.showRelations = false
    },
    approveTemplate (item) {
      crfs.approve('templates', item.uid).then((resp) => {
        this.getTemplates()
      })
    },
    inactivateTemplate (item) {
      crfs.inactivate('templates', item.uid).then((resp) => {
        this.getTemplates()
      })
    },
    reactivateTemplate (item) {
      crfs.reactivate('templates', item.uid).then((resp) => {
        this.getTemplates()
      })
    },
    newTemplateVersion (item) {
      crfs.newVersion('templates', item.uid).then((resp) => {
        this.getTemplates()
      })
    },
    deleteTemplate (item) {
      crfs.delete('templates', item.uid).then((resp) => {
        this.getTemplates()
      })
    },
    editTemplate (item) {
      this.selectedTemplate = item
      this.showForm = true
    },
    openTemplateHistory (item) {
      this.showTemplateHistory = true
      this.templateHistory = item
    },
    closeTemplateHistory () {
      this.showTemplateHistory = false
      this.templateHistory = null
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
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      crfs.get('templates', { params }).then((resp) => {
        this.templates = resp.data.items
        this.total = resp.data.total
      })
    }
  },
  watch: {
    options: {
      handler () {
        this.getTemplates()
      },
      deep: true
    }
  }
}
</script>
