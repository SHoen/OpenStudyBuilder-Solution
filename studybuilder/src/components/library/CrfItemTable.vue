<template>
<div>
  <n-n-table
    :headers="headers"
    :items="items"
    item-key="uid"
    sort-desc
    has-api
    column-data-resource="concepts/odms/items"
    export-data-url="concepts/odms/items"
    :options.sync="options"
    :server-items-length="total"
    @filter="getItems"
    has-history
    >
    <template v-slot:actions="">
      <v-btn
        class="ml-2"
        fab
        dark
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('CRFItems.add_title')"
        data-cy="add-crf-item"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.name="{ item }">
      <n-n-parameter-highlighter :name="item.name" :show-prefix-and-postfix="false" />
    </template>
    <template v-slot:item.description="{ item }">
      {{ item.description }}
    </template>
    <template v-slot:item.activities="{ item }">
      {{ item.activities | names }}
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
    <crf-item-form
      @close="closeForm"
      :editItem="editItem"
      class="fullscreen-dialog"
      :readOnly="readOnlyForm"
      />
  </v-dialog>
  <v-dialog v-model="showItemHistory"
            persistent
            max-width="1200px">
    <history-table @close="closeItemHistory" type="crfItem" :item="selectedItem"
                   :title-label="$t('CrfFormTable.singular_title')" />
  </v-dialog>
  <crf-activities-models-link-form
    :open="linkForm"
    @close="closeLinkForm"
    :item-to-link="selectedItem"
    item-type="item" />
  <v-dialog v-model="showRelations"
            max-width="800px"
            persistent>
    <odm-references-tree
      :item="selectedItem"
      type="item"
      @close="closeRelationsTree()"/>
  </v-dialog>
  <v-dialog v-model="showDuplicationForm"
            max-width="800px"
            persistent>
    <crf-duplication-form
      @close="closeDuplicateForm"
      :item="selectedItem"
      type="item"
      />
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import NNTable from '@/components/tools/NNTable'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import StatusChip from '@/components/tools/StatusChip'
import ActionsMenu from '@/components/tools/ActionsMenu'
import crfs from '@/api/crfs'
import CrfItemForm from '@/components/library/CrfItemForm'
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
    NNParameterHighlighter,
    StatusChip,
    ActionsMenu,
    CrfItemForm,
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
          label: this.$t('CrfLinikingForm.link_activities'),
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
          click: this.openItemHistory
        }
      ],
      headers: [
        { text: this.$t('_global.actions'), value: 'actions', width: '5%' },
        { text: this.$t('CRFItems.oid'), value: 'oid' },
        { text: this.$t('_global.relations'), value: 'relations' },
        { text: this.$t('_global.name'), value: 'name' },
        { text: this.$t('CRFItems.type'), value: 'datatype' },
        { text: this.$t('CRFItems.length'), value: 'length' },
        { text: this.$t('CRFItems.sds_name'), value: 'sdsVarName' },
        { text: this.$t('_global.links'), value: 'activities' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.status'), value: 'status' }
      ],
      showForm: false,
      options: {},
      filters: '',
      total: 0,
      items: [],
      selectedItem: null,
      showItemHistory: false,
      editItem: {},
      linkForm: false,
      readOnlyForm: false,
      showRelations: false,
      showDuplicationForm: false
    }
  },
  methods: {
    openDuplicateForm (item) {
      this.selectedItem = item
      this.showDuplicationForm = true
    },
    closeDuplicateForm () {
      this.showDuplicationForm = false
      this.getItems()
    },
    openRelationsTree (item) {
      this.showRelations = true
      this.selectedItem = item
    },
    closeRelationsTree () {
      this.selectedItem = null
      this.showRelations = false
    },
    openForm () {
      this.showForm = true
    },
    closeForm () {
      this.showForm = false
      this.readOnlyForm = false
      this.editItem = {}
      this.getItems()
    },
    approve (item) {
      crfs.approve('items', item.uid).then((resp) => {
        this.getItems()
      })
    },
    async delete (item) {
      let relationships = 0
      await crfs.getItemRelationship(item.uid).then(resp => {
        if (resp.data.OdmItemGroup && resp.data.OdmItemGroup.length > 0) {
          relationships = resp.data.OdmItemGroup.length
        }
      })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue')
      }
      if (relationships > 0 && await this.$refs.confirm.open(`${this.$t('CRFItems.delete_warning_1')} ${relationships} ${this.$t('CRFItems.delete_warning_2')}`, options)) {
        crfs.delete('items', item.uid).then((resp) => {
          this.getItems()
        })
      } else if (relationships === 0) {
        crfs.delete('items', item.uid).then((resp) => {
          this.getItems()
        })
      }
    },
    inactivate (item) {
      crfs.inactivate('items', item.uid).then((resp) => {
        this.getItems()
      })
    },
    reactivate (item) {
      crfs.reactivate('items', item.uid).then((resp) => {
        this.getItems()
      })
    },
    newVersion (item) {
      crfs.newVersion('items', item.uid).then((resp) => {
        this.getItems()
      })
    },
    edit (item) {
      crfs.getItem(item.uid).then((resp) => {
        this.editItem = resp.data
        this.showForm = true
      })
    },
    view (item) {
      crfs.getItem(item.uid).then((resp) => {
        this.editItem = resp.data
        this.readOnlyForm = true
        this.showForm = true
      })
    },
    openItemHistory (item) {
      this.selectedItem = item
      this.showItemHistory = true
    },
    closeItemHistory () {
      this.selectedItem = {}
      this.showItemHistory = false
    },
    openLinkForm (item) {
      this.selectedItem = item
      this.linkForm = true
    },
    closeLinkForm () {
      this.linkForm = false
      this.selectedItem = {}
      this.getItems()
    },
    getItems (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      crfs.get('items', { params }).then((resp) => {
        this.items = resp.data.items
        this.total = resp.data.total
      })
    }
  },
  watch: {
    options: {
      handler () {
        this.getItems()
      },
      deep: true
    }
  }
}
</script>
