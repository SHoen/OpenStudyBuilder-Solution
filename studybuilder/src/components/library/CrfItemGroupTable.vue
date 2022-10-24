<template>
<div>
  <n-n-table
    :headers="headers"
    :items="itemGroups"
    item-key="uid"
    sort-by="name"
    sort-desc
    :options.sync="options"
    :server-items-length="total"
    @filter="getItemGroups"
    has-history
    has-api
    column-data-resource="concepts/odms/item-groups"
    export-data-url="concepts/odms/item-groups"
    >
    <template v-slot:actions="">
      <v-btn
        class="ml-2"
        fab
        dark
        small
        color="primary"
        @click.stop="openForm"
        :title="$t('CRFItemGroups.add_group')"
        data-cy="add-crf-item-group"
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
    <template v-slot:item.activitySubGroups="{ item }">
      {{ item.activitySubGroups | names }}
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
    <crf-item-group-form
      @close="closeForm"
      :editItem="editItem"
      class="fullscreen-dialog"
      :readOnly="readOnlyForm"
      />
  </v-dialog>
  <v-dialog v-model="showGroupHistory"
            persistent
            max-width="1200px">
    <history-table @close="closeGroupHistory" type="crfGroup" :item="selectedGroup"
                   :title-label="$t('CrfFormTable.singular_title')" />
  </v-dialog>
  <crf-activities-models-link-form
    :open="linkForm"
    @close="closeLinkForm"
    :item-to-link="selectedGroup"
    item-type="itemGroup" />
  <v-dialog v-model="showRelations"
            max-width="800px"
            persistent>
    <odm-references-tree
      :item="selectedGroup"
      type="group"
      @close="closeRelationsTree()"/>
  </v-dialog>
  <v-dialog v-model="showDuplicationForm"
            persistent>
    <crf-duplication-form
      @close="closeDuplicateForm"
      :item="selectedGroup"
      type="group"
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
import CrfItemGroupForm from '@/components/library/CrfItemGroupForm'
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
    CrfItemGroupForm,
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
          label: this.$t('CrfLinikingForm.link_activity_sub_groups'),
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
          click: this.openGroupHistory
        }
      ],
      headers: [
        { text: this.$t('_global.actions'), value: 'actions', width: '5%' },
        { text: this.$t('CRFItemGroups.oid'), value: 'oid' },
        { text: this.$t('_global.relations'), value: 'relations' },
        { text: this.$t('_global.name'), value: 'name' },
        { text: this.$t('CRFItemGroups.repeating'), value: 'repeating' },
        { text: this.$t('_global.description'), value: 'descriptionEngDescription' },
        { text: this.$t('_global.links'), value: 'activitySubGroups' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.status'), value: 'status' }
      ],
      showForm: false,
      showHistory: false,
      selectedGroup: null,
      options: {},
      filters: '',
      total: 0,
      itemGroups: [],
      editItem: {},
      showGroupHistory: false,
      linkForm: false,
      readOnlyForm: false,
      showRelations: false,
      showDuplicationForm: false
    }
  },
  methods: {
    openDuplicateForm (item) {
      this.selectedGroup = item
      this.showDuplicationForm = true
    },
    closeDuplicateForm () {
      this.showDuplicationForm = false
      this.getItemGroups()
    },
    openRelationsTree (item) {
      this.showRelations = true
      this.selectedGroup = item
    },
    closeRelationsTree () {
      this.selectedGroup = null
      this.showRelations = false
    },
    approve (item) {
      crfs.approve('item-groups', item.uid).then((resp) => {
        this.getItemGroups()
      })
    },
    async delete (item) {
      let relationships = 0
      await crfs.getGroupRelationship(item.uid).then(resp => {
        if (resp.data.OdmForm && resp.data.OdmForm.length > 0) {
          relationships = resp.data.OdmForm.length
        }
      })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue')
      }
      if (relationships > 0 && await this.$refs.confirm.open(`${this.$t('CRFItemGroups.delete_warning_1')} ${relationships} ${this.$t('CRFItemGroups.delete_warning_2')}`, options)) {
        crfs.delete('item-groups', item.uid).then((resp) => {
          this.getItemGroups()
        })
      } else if (relationships === 0) {
        crfs.delete('item-groups', item.uid).then((resp) => {
          this.getItemGroups()
        })
      }
    },
    inactivate (item) {
      crfs.inactivate('item-groups', item.uid).then((resp) => {
        this.getItemGroups()
      })
    },
    reactivate (item) {
      crfs.reactivate('item-groups', item.uid).then((resp) => {
        this.getItemGroups()
      })
    },
    newVersion (item) {
      crfs.newVersion('item-groups', item.uid).then((resp) => {
        this.getItemGroups()
      })
    },
    edit (item) {
      crfs.getItemGroup(item.uid).then((resp) => {
        this.editItem = resp.data
        this.showForm = true
      })
    },
    view (item) {
      crfs.getItemGroup(item.uid).then((resp) => {
        this.editItem = resp.data
        this.readOnlyForm = true
        this.showForm = true
      })
    },
    openForm () {
      this.showForm = true
    },
    openGroupHistory (form) {
      this.selectedGroup = form
      this.showGroupHistory = true
    },
    closeGroupHistory () {
      this.selectedGroup = {}
      this.showGroupHistory = false
    },
    closeForm () {
      this.showForm = false
      this.readOnlyForm = false
      this.editItem = {}
      this.getItemGroups()
    },
    openLinkForm (item) {
      this.selectedGroup = item
      this.linkForm = true
    },
    closeLinkForm () {
      this.linkForm = false
      this.selectedGroup = {}
      this.getItemGroups()
    },
    getItemGroups (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      crfs.get('item-groups', { params }).then((resp) => {
        this.itemGroups = resp.data.items
        this.total = resp.data.total
      })
    }
  },
  watch: {
    options: {
      handler () {
        this.getItemGroups()
      },
      deep: true
    }
  }
}
</script>
