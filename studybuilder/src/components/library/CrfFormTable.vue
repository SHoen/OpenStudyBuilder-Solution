<template>
<div>
  <n-n-table
    :headers="headers"
    :items="forms"
    item-key="uid"
    sort-by="name"
    sort-desc
    :options.sync="options"
    :server-items-length="total"
    @filter="getForms"
    has-history
    has-api
    column-data-resource="concepts/odms/forms"
    export-data-url="concepts/odms/forms"
    >
    <template v-slot:actions="">
      <v-btn
        class="ml-2"
        fab
        dark
        small
        color="primary"
        @click.stop="openForm"
        :title="$t('CRFForms.add_form')"
        data-cy="add-crf-form"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.name="{ item }">
      {{ item.name }}
    </template>
    <template v-slot:item.repeating="{ item }">
      {{ item.repeating }}
    </template>
    <template v-slot:item.descriptionEngDescription="{ item }">
      <div v-html="item.descriptionEngDescription"/>
    </template>
    <template v-slot:item.activityGroups="{ item }">
      {{ item.activityGroups | names }}
    </template>
    <template v-slot:item.status="{ item }">
      <status-chip :status="item.status" />
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
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
  <v-dialog
    v-model="showForm"
    persistent
    content-class="fullscreen-dialog"
    >
    <crf-form-form
      @close="closeForm"
      :editItem="editItem"
      class="fullscreen-dialog"
      :readOnly="readOnlyForm"
      />
  </v-dialog>
  <v-dialog v-model="showFormHistory"
            persistent
            max-width="1200px">
    <history-table @close="closeFormHistory" type="crfForm" :item="selectedForm"
                   :title-label="$t('CrfFormTable.singular_title')" />
  </v-dialog>
  <crf-activities-models-link-form
    :open="linkForm"
    @close="closeLinkForm"
    :item-to-link="selectedForm"
    item-type="form" />
  <v-dialog v-model="showRelations"
            max-width="800px"
            persistent>
    <odm-references-tree
      :item="selectedForm"
      type="form"
      @close="closeRelationsTree()"/>
  </v-dialog>
  <v-dialog v-model="showDuplicationForm"
            persistent>
    <crf-duplication-form
      @close="closeDuplicateForm"
      :item="selectedForm"
      type="form"
      />
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import NNTable from '@/components/tools/NNTable'
import StatusChip from '@/components/tools/StatusChip'
import ActionsMenu from '@/components/tools/ActionsMenu'
import crfs from '@/api/crfs'
import CrfFormForm from '@/components/library/CrfFormForm'
import HistoryTable from '@/components/library/HistoryTable'
import CrfActivitiesModelsLinkForm from '@/components/library/CrfActivitiesModelsLinkForm'
import constants from '@/constants/statuses'
import filteringParameters from '@/utils/filteringParameters'
import OdmReferencesTree from '@/components/library/OdmReferencesTree.vue'
import CrfDuplicationForm from '@/components/library/CrfDuplicationForm'
import ConfirmDialog from '@/components/tools/ConfirmDialog'

export default {
  components: {
    NNTable,
    StatusChip,
    ActionsMenu,
    CrfFormForm,
    HistoryTable,
    CrfActivitiesModelsLinkForm,
    OdmReferencesTree,
    CrfDuplicationForm,
    ConfirmDialog
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) => item.possibleActions.find(action => action === 'approve'),
          click: this.approve
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'edit'),
          click: this.edit
        },
        {
          label: this.$t('_global.view'),
          icon: 'mdi-eye-outline',
          iconColor: 'primary',
          condition: (item) => item.status === constants.FINAL,
          click: this.view
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'newVersion'),
          click: this.newVersion
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'inactivate'),
          click: this.inactivate
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'reactivate'),
          click: this.reactivate
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => item.possibleActions.find(action => action === 'delete'),
          click: this.delete
        },
        {
          label: this.$t('CrfLinikingForm.link_activity_groups'),
          icon: 'mdi-plus',
          iconColor: 'primary',
          condition: (item) => item.status === constants.FINAL,
          click: this.openLinkForm
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
          click: this.openFormHistory
        }
      ],
      headers: [
        { text: this.$t('_global.actions'), value: 'actions', width: '5%' },
        { text: this.$t('CRFForms.oid'), value: 'oid' },
        { text: this.$t('_global.relations'), value: 'relations' },
        { text: this.$t('_global.name'), value: 'name' },
        { text: this.$t('CrfFormTable.repeating'), value: 'repeating' },
        { text: this.$t('_global.description'), value: 'descriptionEngDescription' },
        { text: this.$t('_global.links'), value: 'activityGroups' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.status'), value: 'status' }
      ],
      showForm: false,
      showHistory: false,
      selectedForm: null,
      options: {},
      filters: '',
      total: 0,
      forms: [],
      editItem: {},
      showFormHistory: false,
      linkForm: false,
      readOnlyForm: false,
      showRelations: false,
      showDuplicationForm: false
    }
  },
  methods: {
    openDuplicateForm (item) {
      this.selectedForm = item
      this.showDuplicationForm = true
    },
    closeDuplicateForm () {
      this.showDuplicationForm = false
      this.getForms()
    },
    openRelationsTree (item) {
      this.showRelations = true
      this.selectedForm = item
    },
    closeRelationsTree () {
      this.selectedForm = null
      this.showRelations = false
    },
    approve (item) {
      crfs.approve('forms', item.uid).then((resp) => {
        this.getForms()
      })
    },
    async delete (item) {
      let relationships = 0
      await crfs.getFormRelationship(item.uid).then(resp => {
        if (resp.data.OdmTemplate && resp.data.OdmTemplate.length > 0) {
          relationships = resp.data.OdmTemplate.length
        }
      })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue')
      }
      if (relationships > 0 && await this.$refs.confirm.open(`${this.$t('CRFForms.delete_warning_1')} ${relationships} ${this.$t('CRFForms.delete_warning_2')}`, options)) {
        crfs.delete('forms', item.uid).then((resp) => {
          this.getForms()
        })
      } else if (relationships === 0) {
        crfs.delete('forms', item.uid).then((resp) => {
          this.getForms()
        })
      }
    },
    inactivate (item) {
      crfs.inactivate('forms', item.uid).then((resp) => {
        this.getForms()
      })
    },
    reactivate (item) {
      crfs.reactivate('forms', item.uid).then((resp) => {
        this.getForms()
      })
    },
    newVersion (item) {
      crfs.newVersion('forms', item.uid).then((resp) => {
        this.getForms()
      })
    },
    edit (item) {
      crfs.getForm(item.uid).then((resp) => {
        this.editItem = resp.data
        this.showForm = true
      })
    },
    view (item) {
      crfs.getForm(item.uid).then((resp) => {
        this.editItem = resp.data
        this.readOnlyForm = true
        this.showForm = true
      })
    },
    openForm () {
      this.showForm = true
    },
    closeForm () {
      this.showForm = false
      this.readOnlyForm = false
      this.editItem = {}
      this.getForms()
    },
    openFormHistory (form) {
      this.selectedForm = form
      this.showFormHistory = true
    },
    closeFormHistory () {
      this.selectedForm = {}
      this.showFormHistory = false
    },
    openLinkForm (item) {
      this.selectedForm = item
      this.linkForm = true
    },
    closeLinkForm () {
      this.linkForm = false
      this.selectedForm = {}
      this.getForms()
    },
    getForms (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      crfs.get('forms', { params }).then((resp) => {
        this.forms = resp.data.items
        this.total = resp.data.total
      })
    }
  },
  watch: {
    options: {
      handler () {
        this.getForms()
      },
      deep: true
    }
  }
}
</script>
