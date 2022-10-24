<template>
<div>
  <n-n-table
    :headers="headers"
    :items="compoundAliases"
    :server-items-length="total"
    :options.sync="options"
    item-key="uid"
    dense
    has-api
    @filter="fetchItems"
    column-data-resource="concepts/compound-aliases"
    export-data-url="concepts/compound-aliases"
    export-object-label="compound-aliases"
    >
    <template v-slot:actions="">
      <v-btn
        fab
        dark
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('CompoundAliasForm.add_title')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu
        :actions="actions"
        :item="item"
        />
    </template>
    <template v-slot:item.isPreferredSynonym="{ item }">
      {{ item.isPreferredSynonym|yesno }}
    </template>
    <template v-slot:item.name="{ item }">
      <router-link :to="{ name: 'CompoundOverview', params: { id: item.compound.uid } }">
        {{ item.name }}
      </router-link>
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate|date }}
    </template>
    <template v-slot:item.status="{ item }">
      <status-chip :status="item.status" />
    </template>
  </n-n-table>
  <v-dialog
    v-model="showForm"
    fullscreen
    persistent
    content-class="fullscreen-dialog"
    >
    <compound-alias-form
      @close="closeForm"
      @created="fetchItems"
      @updated="fetchItems"
      :compound-alias-uid="selectedItem ? selectedItem.uid : null"
      :formShown="showForm"
      />
  </v-dialog>
  <v-dialog
    v-model="showHistory"
    persistent
    max-width="1200px"
    >
    <history-table
      @close="closeHistory"
      type="compoundAlias"
      url-prefix="compound-aliases"
      :item="selectedItem"
      :title-label="$t('CompoundAliasTable.compound_alias')"
      />
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu'
import { bus } from '@/main'
import CompoundAliasForm from './CompoundAliasForm'
import compoundAliases from '@/api/concepts/compoundAliases'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import HistoryTable from '@/components/library/HistoryTable'
import NNTable from '@/components/tools/NNTable'
import StatusChip from '@/components/tools/StatusChip'

export default {
  components: {
    ActionsMenu,
    CompoundAliasForm,
    ConfirmDialog,
    HistoryTable,
    NNTable,
    StatusChip
  },
  props: {
    tabClickedAt: Number
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'edit'),
          click: this.editItem
        },
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) => item.possibleActions.find(action => action === 'approve'),
          click: this.approveItem
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
          click: this.inactivateItem
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'reactivate'),
          click: this.reactivateItem
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => item.possibleActions.find(action => action === 'delete'),
          click: this.deleteItem
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory
        }
      ],
      compoundAliases: [],
      filters: {},
      sort: {},
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('CompoundAliasTable.compound_name'), value: 'compound.name' },
        { text: this.$t('_global.name'), value: 'name' },
        { text: this.$t('_global.sentence_case_name'), value: 'nameSentenceCase' },
        { text: this.$t('CompoundAliasTable.is_preferred_synonym'), value: 'isPreferredSynonym' },
        { text: this.$t('_global.definition'), value: 'definition' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.status'), value: 'status' }
      ],
      options: {},
      selectedItem: null,
      showForm: false,
      showHistory: false,
      total: 0
    }
  },
  methods: {
    fetchItems (filters, sort, filtersUpdated) {
      if (filters !== undefined) {
        this.filters = filters
      }
      if (sort !== undefined) {
        this.sort = sort
      }
      if (filtersUpdated) {
        this.options.page = 1
      }
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      if (this.filters !== undefined) {
        params.filters = this.filters
      }
      if (this.options.sortBy.length !== 0 && this.sort !== undefined) {
        params.sortBy = `{"${this.options.sortBy[0]}":${!this.sort}}`
      }
      compoundAliases.getFiltered(params).then(resp => {
        this.compoundAliases = resp.data.items
        this.total = resp.data.total
      })
    },
    closeForm () {
      this.showForm = false
      this.selectedItem = null
    },
    editItem (item) {
      this.selectedItem = item
      this.showForm = true
    },
    approveItem (item) {
      compoundAliases.approve(item.uid).then(resp => {
        this.fetchItems()
        bus.$emit('notification', { msg: this.$t('CompoundAliasTable.approve_success'), type: 'success' })
      })
    },
    async deleteItem (item) {
      const options = { type: 'warning' }
      const compoundAlias = item.name
      if (await this.$refs.confirm.open(this.$t('CompoundAliasTable.confirm_delete', { compoundAlias }), options)) {
        await compoundAliases.deleteObject(item.uid)
        this.fetchItems()
        bus.$emit('notification', { msg: this.$t('CompoundAliasTable.delete_success'), type: 'success' })
      }
    },
    createNewVersion (item) {
      compoundAliases.newVersion(item.uid).then(resp => {
        this.fetchItems()
        bus.$emit('notification', { msg: this.$t('CompoundAliasTable.new_version_success'), type: 'success' })
      })
    },
    inactivateItem (item) {
      compoundAliases.inactivate(item.uid).then(resp => {
        this.fetchItems()
        bus.$emit('notification', { msg: this.$t('CompoundAliasTable.inactivate_success'), type: 'success' })
      })
    },
    reactivateItem (item) {
      compoundAliases.reactivate(item.uid).then(resp => {
        this.fetchItems()
        bus.$emit('notification', { msg: this.$t('CompoundAliasTable.reactivate_success'), type: 'success' })
      })
    },
    openHistory (item) {
      this.selectedItem = item
      this.showHistory = true
    },
    closeHistory () {
      this.showHistory = false
    }
  },
  mounted () {
    this.fetchItems()
  },
  watch: {
    tabClickedAt (value) {
      this.fetchItems()
    }
  }
}
</script>
