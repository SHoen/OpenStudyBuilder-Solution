<template>
<div>
  <n-n-table
    :headers="headers"
    :items="compounds"
    :server-items-length="total"
    :options.sync="options"
    item-key="uid"
    dense
    has-api
    @filter="fetchItems"
    column-data-resource="concepts/compounds"
    export-data-url="concepts/compounds"
    export-object-label="compounds"
    >
    <template v-slot:actions="">
      <v-btn
        fab
        dark
        small
        color="primary"
        @click.stop="showCompoundForm = true"
        :title="$t('CompoundForm.add_title')"
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
    <template v-slot:item.isSponsorCompound="{ item }">
      {{ item.isSponsorCompound|yesno }}
    </template>
    <template v-slot:item.name="{ item }">
      <router-link :to="{ name: 'CompoundOverview', params: { id: item.uid } }">
        {{ item.name }}
      </router-link>
    </template>
    <template v-slot:item.isNameInn="{ item }">
      {{ item.isNameInn|yesno }}
    </template>
    <template v-slot:item.brands="{ item }">
      {{ item.brands|names }}
    </template>
    <template v-slot:item.substances="{ item }">
      {{ item.substances|substances }}
    </template>
    <template v-slot:item.pharmacologicalClasses="{ item }">
      {{ item.substances|pharmacologicalClasses }}
    </template>
    <template v-slot:item.doseValues="{ item }">
      {{ item.doseValues|numericValues }}
    </template>
    <template v-slot:item.strengthValues="{ item }">
      {{ item.strengthValues|numericValues }}
    </template>
    <template v-slot:item.dosageForms="{ item }">
      {{ item.dosageForms|names }}
    </template>
    <template v-slot:item.routesOfAdministration="{ item }">
      {{ item.routesOfAdministration|names }}
    </template>
    <template v-slot:item.doseFrequencies="{ item }">
      {{ item.doseFrequencies|names }}
    </template>
    <template v-slot:item.dispensers="{ item }">
      {{ item.dispensers|names }}
    </template>
    <template v-slot:item.deliveryDevices="{ item }">
      {{ item.deliveryDevices|names }}
    </template>
    <template v-slot:item.halfLife="{ item }">
      <template v-if="item.halfLife">
        {{ item.halfLife.value }} {{ item.halfLife.unitLabel }}
      </template>
    </template>
    <template v-slot:item.lagTimes="{ item }">
      {{ item.lagTimes|lagTimes }}
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate|date }}
    </template>
    <template v-slot:item.status="{ item }">
      <status-chip :status="item.status" />
    </template>
  </n-n-table>
  <v-dialog
    v-model="showCompoundForm"
    fullscreen
    persistent
    content-class="fullscreen-dialog"
    >
    <compound-form
      @close="closeCompoundForm"
      @created="fetchItems"
      @updated="fetchItems"
      :compound-uid="selectedCompound ? selectedCompound.uid : null"
      :formShown="showCompoundForm"
      />
  </v-dialog>
  <v-dialog
    v-model="showHistory"
    persistent
    max-width="1200px"
    >
    <history-table
      @close="closeHistory"
      type="compound"
      url-prefix="compounds"
      :item="selectedCompound"
      :title-label="$t('CompoundTable.compound')"
      />
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu'
import { bus } from '@/main'
import CompoundForm from './CompoundForm'
import compounds from '@/api/concepts/compounds'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import HistoryTable from '@/components/library/HistoryTable'
import NNTable from '@/components/tools/NNTable'
import StatusChip from '@/components/tools/StatusChip'

export default {
  components: {
    ActionsMenu,
    CompoundForm,
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
          click: this.editCompound
        },
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) => item.possibleActions.find(action => action === 'approve'),
          click: this.approveCompound
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
          click: this.inactivateCompound
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'reactivate'),
          click: this.reactivateCompound
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => item.possibleActions.find(action => action === 'delete'),
          click: this.deleteCompound
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory
        }
      ],
      compounds: [],
      filters: {},
      sort: {},
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('CompoundTable.sponsor_compound'), value: 'isSponsorCompound' },
        { text: this.$t('CompoundTable.compound_name'), value: 'name' },
        { text: this.$t('CompoundTable.is_name_inn'), value: 'isNameInn' },
        { text: this.$t('CompoundTable.nnc_number_long'), value: 'nncLongNumber' },
        { text: this.$t('CompoundTable.nnc_number_short'), value: 'nncShortNumber' },
        { text: this.$t('CompoundTable.analyte_number'), value: 'analyteNumber' },
        { text: this.$t('_global.definition'), value: 'definition' },
        { text: this.$t('CompoundTable.brand_name'), value: 'brands' },
        { text: this.$t('CompoundTable.substance_name'), value: 'substances' },
        { text: this.$t('CompoundTable.pharmacological_class'), value: 'pharmacologicalClasses' },
        { text: this.$t('CompoundTable.dose'), value: 'doseValues' },
        { text: this.$t('CompoundTable.strength'), value: 'strengthValues' },
        { text: this.$t('CompoundTable.dosage_form'), value: 'dosageForms' },
        { text: this.$t('CompoundTable.route_of_admin'), value: 'routesOfAdministration' },
        { text: this.$t('CompoundTable.dose_frequency'), value: 'doseFrequencies' },
        { text: this.$t('CompoundTable.dispensed_in'), value: 'dispensers' },
        { text: this.$t('CompoundTable.delivery_device'), value: 'deliveryDevices' },
        { text: this.$t('CompoundTable.half_life'), value: 'halfLife' },
        { text: this.$t('CompoundTable.lag_time'), value: 'lagTimes' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.status'), value: 'status' }
      ],
      options: {},
      selectedCompound: null,
      showCompoundForm: false,
      showHistory: false,
      total: 0
    }
  },
  filters: {
    numericValues: function (value) {
      return value.map(item => `${item.value} ${item.unitLabel}`).join(', ')
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
      compounds.getFiltered(params).then(resp => {
        this.compounds = resp.data.items
        this.total = resp.data.total
      })
    },
    closeCompoundForm () {
      this.showCompoundForm = false
      this.selectedCompound = null
    },
    editCompound (item) {
      this.selectedCompound = item
      this.showCompoundForm = true
    },
    approveCompound (item) {
      compounds.approve(item.uid).then(resp => {
        this.fetchItems()
        bus.$emit('notification', { msg: this.$t('CompoundTable.approve_success'), type: 'success' })
      })
    },
    async deleteCompound (item) {
      const options = { type: 'warning' }
      const compound = item.name
      if (await this.$refs.confirm.open(this.$t('CompoundTable.confirm_delete', { compound }), options)) {
        await compounds.deleteObject(item.uid)
        this.fetchItems()
        bus.$emit('notification', { msg: this.$t('CompoundTable.delete_success'), type: 'success' })
      }
    },
    createNewVersion (item) {
      compounds.newVersion(item.uid).then(resp => {
        this.fetchItems()
        bus.$emit('notification', { msg: this.$t('CompoundTable.new_version_success'), type: 'success' })
      })
    },
    inactivateCompound (item) {
      compounds.inactivate(item.uid).then(resp => {
        this.fetchItems()
        bus.$emit('notification', { msg: this.$t('CompoundTable.inactivate_success'), type: 'success' })
      })
    },
    reactivateCompound (item) {
      compounds.reactivate(item.uid).then(resp => {
        this.fetchItems()
        bus.$emit('notification', { msg: this.$t('CompoundTable.reactivate_success'), type: 'success' })
      })
    },
    openHistory (item) {
      this.selectedCompound = item
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
      this.fetchItems(this.filters, this.sort)
    }
  }
}
</script>
