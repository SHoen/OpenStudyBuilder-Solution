<template>
<div>
  <n-n-table
    :headers="headers"
    :items="units"
    item-key="uid"
    sort-by="startDate"
    sort-desc
    has-api
    export-data-url="concepts/unit-definitions"
    column-data-resource="concepts/unit-definitions"
    :options.sync="options"
    :server-items-length="total"
    @filter="getUnits"
    >
    <template v-slot:actions="">
      <v-btn
        class="ml-2"
        fab
        dark
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('UnitForm.add_title')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.masterUnit="{ item }">
      {{ item.masterUnit|yesno }}
    </template>
    <template v-slot:item.displayUnit="{ item }">
      {{ item.displayUnit|yesno }}
    </template>
    <template v-slot:item.unitSubsets="{ item }">
      {{ displayList(item.unitSubsets) }}
    </template>
    <template v-slot:item.ctUnits="{ item }">
      {{ displayList(item.ctUnits) }}
    </template>
    <template v-slot:item.convertibleUnit="{ item }">
      {{ item.convertibleUnit|yesno }}
    </template>
    <template v-slot:item.siUnit="{ item }">
      {{ item.siUnit|yesno }}
    </template>
    <template v-slot:item.usConventionalUnit="{ item }">
      {{ item.usConventionalUnit|yesno }}
    </template>
    <template v-slot:item.status="{ item }">
      <status-chip :status="item.status" />
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate | date }}
    </template>
    <template v-slot:item.ucumUnit="{ item }">
      <v-edit-dialog
        :return-value.sync="item.ucumUnit"
        >
        <span v-if="item.ucumUnit">{{ item.ucumUnit.code }}</span>
        <v-icon v-else>mdi-table-search</v-icon>
        <template v-slot:input>
          <ucum-unit-field
            v-model="item.ucumUnit"
            />
        </template>
      </v-edit-dialog>
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
  </n-n-table>
  <unit-form
    :open="showForm"
    @close="close()"
    :unit="activeUnit"/>
</div>
</template>

<script>
import NNTable from '@/components/tools/NNTable'
import StatusChip from '@/components/tools/StatusChip'
import UnitForm from '@/components/library/UnitForm'
import ActionsMenu from '@/components/tools/ActionsMenu'
import StudybuilderUCUMField from '@/components/tools/StudybuilderUCUMField'
import units from '@/api/units'

export default {
  components: {
    NNTable,
    StatusChip,
    'ucum-unit-field': StudybuilderUCUMField,
    UnitForm,
    ActionsMenu
  },
  data () {
    return {
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('_global.library'), value: 'libraryName' },
        { text: this.$t('_global.name'), value: 'name' },
        { text: this.$t('UnitTable.master_unit'), value: 'masterUnit' },
        { text: this.$t('UnitTable.display_unit'), value: 'displayUnit' },
        { text: this.$t('UnitTable.unit_subsets'), value: 'unitSubsets' },
        { text: this.$t('UnitTable.ucum_unit'), value: 'ucum.name' },
        { text: this.$t('UnitTable.ct_units'), value: 'ctUnits', width: '10%' },
        { text: this.$t('UnitTable.convertible_unit'), value: 'convertibleUnit' },
        { text: this.$t('UnitTable.si_unit'), value: 'siUnit' },
        { text: this.$t('UnitTable.us_conventional_unit'), value: 'usConventionalUnit' },
        { text: this.$t('UnitTable.unit_dimension'), value: 'unitDimension.name' },
        { text: this.$t('UnitTable.legacy_code'), value: 'legacyCode' },
        { text: this.$t('UnitTable.molecular_weight'), value: 'molecularWeightConvExpon' },
        { text: this.$t('UnitTable.conversion_factor'), value: 'conversionFactorToMaster' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' }
      ],
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.status === 'Draft',
          click: this.editUnit
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => (item.status === 'Draft' && parseFloat(item.version) < 1),
          click: this.deleteUnit
        },
        {
          label: this.$t('_global.new_version'),
          icon: 'mdi-plus-circle-outline',
          iconColor: 'primary',
          condition: (item) => item.status === 'Final',
          click: this.newUnitVersion
        },
        {
          label: this.$t('_global.approve'),
          icon: 'mdi-check-decagram',
          iconColor: 'success',
          condition: (item) => item.status === 'Draft',
          click: this.approveUnit
        },
        {
          label: this.$t('_global.inactivate'),
          icon: 'mdi-close-octagon-outline',
          iconColor: 'primary',
          condition: (item) => item.status === 'Final',
          click: this.inactivateUnit
        },
        {
          label: this.$t('_global.reactivate'),
          icon: 'mdi-undo-variant',
          iconColor: 'primary',
          condition: (item) => item.status === 'Retired',
          click: this.reactivateUnit
        }
      ],
      showForm: false,
      options: {},
      filters: '',
      total: 0,
      units: [],
      activeUnit: {}
    }
  },
  methods: {
    displayList (items) {
      return items.map(item => item.name).join(', ')
    },
    getUnits (filters, sort, filtersUpdated) {
      this.filters = filters
      let data
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      if (filtersUpdated) {
        /* Filters have changed, reset page number */
        this.options.page = 1
      }
      if (this.filters && this.filters !== undefined && filters !== '{}') {
        const filtersObj = JSON.parse(filters)
        if (Object.keys(filtersObj).length !== 0 && filtersObj.constructor === Object) {
          params.filters = JSON.stringify(filtersObj)
        }
      }
      if (this.options.sortBy.length !== 0 && sort !== undefined) {
        params.sortBy = `{"${this.options.sortBy[0]}":${!sort}}`
      } else {
        params.sortBy = `{"startDate":${false}}`
      }
      this.$store.dispatch('units/fetchUnits', { params }).then((resp) => {
        data = this.$store.getters['units/units']
        this.units = data.items
        this.total = data.total
      })
    },
    editUnit (item) {
      this.activeUnit = item
      this.showForm = true
    },
    deleteUnit (item) {
      units.delete(item.uid).then(resp => {
        this.getUnits()
      })
    },
    newUnitVersion (item) {
      units.newVersion(item.uid).then(resp => {
        this.getUnits()
      })
    },
    approveUnit (item) {
      units.approve(item.uid).then(resp => {
        this.getUnits()
      })
    },
    inactivateUnit (item) {
      units.inactivate(item.uid).then(resp => {
        this.getUnits()
      })
    },
    reactivateUnit (item) {
      units.reactivate(item.uid).then(resp => {
        this.getUnits()
      })
    },
    close () {
      this.showForm = false
      this.getUnits()
    }
  },
  watch: {
    options: {
      handler () {
        this.getUnits()
      },
      deep: true
    }
  }
}
</script>
