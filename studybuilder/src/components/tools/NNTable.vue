<template>
<div>
  <v-card :elevation="elevation" class="rounded-0">
    <v-card-title style="z-index: 3; position: relative" class="pt-0 mt-3">
      <template v-if="!hideDefaultSwitches">
        <div :title="$t('NNTableTooltips.select_rows')">
          <v-switch
            data-cy="select-rows"
            v-model="showSelectBoxes"
            :label="$t('NNTable.show_select_boxes_label')"
            class="mr-6"
            hide-details
            :title="$t('NNTableTooltips.select_rows')"
            />
        </div>
      </template>
      <slot name="afterSwitches"></slot>
      <v-spacer />
      <v-spacer />
      <slot name="beforeActions"></slot>
      <div
        v-if="!hideActionsMenu"
        class="mt-3">
        <slot
          name="actions"
          v-bind:showSelectBoxes="showSelectBoxes"
          v-bind:selected="selected"
          >
        </slot>
        <v-btn
          v-if="!disableFiltering && returnHasApi()"
          class="ml-2 white--text"
          fab
          small
          @click="showColumnsToFilterDialog = true"
          color="light-blue darken-4"
          :title="$t('NNTableTooltips.filters')"
          data-cy="filters-button"
          >
          <v-icon>mdi-filter</v-icon>
        </v-btn>
        <v-btn
          v-if="modifiableTable && !onlyTextSearch"
          class="ml-2 white--text"
          fab
          small
          @click="showColumnsDialog = true"
          color="grey darken-3"
          :title="$t('NNTableTooltips.columns_layout')"
          data-cy="columns-layout-button"
          >
          <v-icon>mdi-table-column</v-icon>
        </v-btn>
        <data-table-export-button
          class="ml-2"
          v-if="!hideExportButton"
          :object-label="exportObjectLabel"
          :dataUrl="exportDataUrl"
          :dataUrlParams="exportDataUrlParams"
          :headers="headers"
          :items="(selected.length) ? selected : []"
          @export="confirmExport"
          data-cy="export-data-button"
          />
        <v-btn
          v-if="hasHistory"
          class="ml-2"
          color="secondary"
          fab
          small
          :title="$t('NNTableTooltips.history')"
          >
          <v-icon>mdi-history</v-icon>
        </v-btn>
      </div>
      <slot name="beforeTable"></slot>
    </v-card-title>
    <v-app-bar
      flat
      :class="additionalMargin ? 'pt-1 mt-3' : 'pt-1'"
      color="#e5e5e5"
      style="height: 55px"
      v-if="!disableFiltering"
      >
      <v-text-field
        v-model="search"
        dense
        append-icon="mdi-magnify"
        :label="$t('_global.search')"
        single-line
        hide-details
        style="min-width: 200px; max-width: 300px;"
        class="mr-4 mt-2 pt-0 mb-3 searchFieldLabel"
        @input="fullTextSearch(search)"
        data-cy="search-field"
        v-if="(!hideSearchField && returnHasApi()) || onlyTextSearch"
        />
      <v-spacer></v-spacer>
      <div class="mb-4" v-if="!returnHasApi() && !onlyTextSearch">
        {{ $t('_global.filtering_to_add') }}
      </div>
      <v-slide-group
        multiple
        show-arrows
        v-if="returnHasApi()"
      >
        <v-spacer/>
        <span v-for="(item) in itemsToFilter" :key="item.text">
          <div>
            <filter-autocomplete
              :clearInput="trigger"
              :item="item"
              :filters="filters"
              :trigger="refreshFiltersTrigger"
              @filter="columnFilter"
              :library="library"
              :resource="[columnDataResource, codelistUid]"
              :parameters="columnDataParameters"
              :initial-data="getColumnInitialData(item)"
              :filters-modify-function="filtersModifyFunction"/>
          </div>
        </span>
        <v-btn
          icon
          :title="$t('NNTableTooltips.clear_filters_content')"
          :class="itemsToFilter.length !== 0 ? 'mt-2' : 'mb-3'"
          @click="clearFilters()"
          >
          <v-icon dark>
              mdi-trash-can
          </v-icon>
        </v-btn>
      </v-slide-group>
    </v-app-bar>
    <resizing-div>
      <template v-slot:resizing-area="areaProps">
        <v-data-table
          data-cy="data-table"
          v-model="selected"
          :show-select="showSelectBoxes"
          :items-per-page="computedItemsPerPage"
          :footer-props="returnHasApi() ? {
            'items-per-page-options': [ 100, 15, 10, 5 ]
          } : {}"
          class="py-4 mr-0"
          :item-class="rowClass"
          :loading="loading"
          :items="filteredItems"
          :height="areaProps.areaHeight"
          :search="search"
          :headers="shownColumns"
          @update:page="returnHasApi() ? filterTable() : ''"
          @update:sort-desc="filterTable($event)"
          elevation="0"
          v-bind="$attrs"
          v-on="$listeners"
          :single-expand="singleExpand"
          :fixed-header="fixedHeader"
          :no-data-text="noDataText"
          disable-sort
          >
          <template v-for="header in shownColumns" v-slot:[getHeaderSlotName(header)]>
            <v-row class="headerRow" :key="header.value">
              <v-chip v-if="header.color" small :color="header.color" class="mt-1 mr-1"/>
              <div class="mt-1">{{ header.text }}</div>
              <v-icon v-if="options && options.sortBy[0] === header.value">
                <template v-if="!currentSortDirection">mdi-arrow-up-thin</template>
                <template v-else>mdi-arrow-down-thin</template>
              </v-icon>
              <v-menu offset-y v-if="header.text !== ''">
                <template v-slot:activator="{ on, attrs }">
                  <v-btn
                    icon
                    v-bind="attrs"
                    v-on="on"
                    plain
                    class="pb-1"
                    >
                    <v-icon v-show="header.value==columnValueIndex">mdi-dots-vertical</v-icon>
                  </v-btn>
                </template>
                <v-list v-if="modifiableTable && !onlyTextSearch">
                  <template v-for="(item, index) in headerActions">
                    <v-list-item
                      :key="index"
                      @mouseover="columnValueIndex=header.value" @mouseleave="columnValueIndex=''"
                      v-if="item.available"
                      >
                      <v-btn
                        @click="item.click(header)"
                        text
                        class="disableUpperCase"
                        >
                        {{ (itemsToFilter[itemsToFilter.findIndex(el => el.value === header.value)] && item.label === $t('NNTable.add_to_filter')) ? $t('NNTable.remove_from_filter') : item.label}}
                      </v-btn>
                    </v-list-item>
                  </template>
                </v-list>
              </v-menu>
            </v-row>
          </template>
          <template v-for="(_, slot) of $scopedSlots" v-slot:[slot]="scope">
            <slot :name="slot" v-bind="scope" v-bind:showSelectBoxes="showSelectBoxes" />
          </template>
        </v-data-table>
      </template>
    </resizing-div>
  </v-card>

  <v-dialog
    v-model="showColumnsDialog"
    max-width="550"
    persistent
    content-class="upperRight"
    tile
    >
    <column-choosing-form
      key="columnsForm"
      data-cy="show-columns-form"
      :availableColumns="headers"
      :tableName="$route.fullPath"
      @save="saveSelectedColumns"
      @close="showColumnsDialog = false"
      :title="$t('ColumnChoosingForm.columnsTitle')"
      :restoreLabel="$t('ColumnChoosingForm.show_all_label')"
      />
  </v-dialog>

  <v-dialog
    v-model="showColumnsToFilterDialog"
    max-width="550"
    persistent
    content-class="upperRight"
    tile
    >
    <column-choosing-form
      key="filtersForm"
      data-cy="filters-select-form"
      :availableColumns="headers"
      :alreadyInFilter="itemsToFilter"
      filtering
      :tableName="''"
      @save="saveSelectedColumnsToFilter"
      @clear="clearData()"
      @close="showColumnsToFilterDialog = false"
      :title="$t('ColumnChoosingForm.filtersTitle')"
      :restoreLabel="$t('ColumnChoosingForm.clear_label')"
      />
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import ColumnChoosingForm from '@/components/tools/ColumnChoosingForm'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import DataTableExportButton from '@/components/tools/DataTableExportButton'
import FilterAutocomplete from '../tools/FilterAutocomplete.vue'
import ResizingDiv from './ResizingDiv.vue'
import i18n from '@/plugins/i18n'

export default {
  components: {
    ColumnChoosingForm,
    ConfirmDialog,
    DataTableExportButton,
    FilterAutocomplete,
    ResizingDiv
  },
  props: {
    headers: Array,
    defaultHeaders: Array,
    items: Array,
    hideDefaultSwitches: {
      type: Boolean,
      default: false
    },
    hideActionsMenu: {
      type: Boolean,
      default: false
    },
    hideExportButton: {
      type: Boolean,
      default: false
    },
    exportObjectLabel: {
      type: String,
      required: false
    },
    exportDataUrl: {
      type: String,
      required: false
    },
    exportDataUrlParams: {
      type: Object,
      required: false
    },
    hasApi: {
      type: Boolean,
      default: false
    },
    hideSearchField: {
      type: Boolean,
      default: false
    },
    elevation: {
      type: String,
      default: '0'
    },
    showSelect: {
      type: Boolean,
      default: false
    },
    showFilterBarByDefault: {
      type: Boolean,
      default: false
    },
    itemsPerPage: {
      type: Number,
      required: false
    },
    options: Object,
    columnDataResource: String,
    columnDataParameters: Object,
    initialColumnData: Object,
    codelistUid: String,
    subTables: {
      type: Boolean,
      default: false
    },
    hasHistory: {
      type: Boolean,
      default: false
    },
    disableFiltering: {
      type: Boolean,
      default: false
    },
    library: String,
    noDataText: {
      type: String,
      default: () => i18n.t('NNTable.no_data')
    },
    filtersModifyFunction: {
      type: Function,
      required: false
    },
    additionalMargin: {
      type: Boolean,
      default: false
    },
    modifiableTable: {
      type: Boolean,
      default: true
    },
    fixedHeader: {
      type: Boolean,
      default: true
    },
    onlyTextSearch: {
      type: Boolean,
      default: false
    },
    singleExpand: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    ...mapGetters({
      userData: 'app/userData',
      columns: 'tablesLayout/columns'
    }),
    filteredItems () {
      if (this.hasApi) {
        return this.items
      }
      return this.items.filter((d) => {
        return Object.keys(this.data).every((f) => {
          if (Date.parse(new Date(this.data[f][0])) && this.data[f].length > 0) {
            const split = f.split('.')
            if (split.length > 1) {
              return this.data[f].length < 1 || (this.data[f][0] <= d[split[0]][split[1]] && this.data[f][1] >= d[split[0]][split[1]]) || this.data[f].includes(d[split[0]][split[1]].substring(0, 10))
            } else {
              return this.data[f].length < 1 || (this.data[f][0] <= d[f] && this.data[f][1] >= d[f]) || this.data[f].includes(d[f].substring(0, 10))
            }
          } else {
            return this.data[f].length < 1 || this.data[f].includes(d[f])
          }
        })
      })
    },
    computedItemsPerPage () {
      return this.itemsPerPage ? this.itemsPerPage : this.userData.rows
    }
  },
  mounted () {
    this.$store.commit('tablesLayout/INITIATE_COLUMNS')
    if (!this.columns[this.$route.fullPath] || this.columns[this.$route.fullPath].length === 0) {
      if (this.defaultHeaders && this.defaultHeaders.length !== 0) {
        this.shownColumns = this.defaultHeaders
      } else {
        this.shownColumns = JSON.parse(JSON.stringify(this.headers))
      }
    } else {
      this.shownColumns = this.columns[this.$route.fullPath]
      const check = new Set()
      this.shownColumns = this.shownColumns.filter(obj => !check.has(obj.value) && check.add(obj.value))
    }
    if (this.showFilterBarByDefault) {
      this.itemsToFilter = this.headers.filter(header => header.value !== 'actions')
    }
    if (this.items && this.items.length) {
      this.loading = false
    }
  },
  updated () {
    const headers = document.querySelectorAll('div[class*="v-window-item--active"] th')
    for (let index = 0; index < this.shownColumns.length; index++) {
      const header = headers[index]
      if (!header) {
        continue
      }
      header.addEventListener('mouseover', () => {
        this.columnValueIndex = this.shownColumns[index].value
      })
      header.addEventListener('mouseleave', () => {
        this.columnValueIndex = ''
      })
    }
  },
  data () {
    return {
      columnValueIndex: '',
      actionsMenu: false,
      loading: true,
      showSelectBoxes: false,
      showFilterBar: false,
      newColumnToFilter: false,
      showColumnsDialog: false,
      shownColumns: [],
      selected: [],
      search: '',
      itemsToFilter: [],
      data: {
        name: []
      },
      menu: false,
      date: [],
      apiParams: new Map(),
      filters: '{}',
      trigger: 0,
      refreshFiltersTrigger: 0,
      showColumnsToFilterDialog: false,
      currentSortDirection: true,
      headerActions: [
        {
          label: this.$t('NNTable.sort_asc'),
          click: this.sortAscending,
          available: this.returnHasApi()
        },
        {
          label: this.$t('NNTable.sort_desc'),
          click: this.sortDescending,
          available: this.returnHasApi()
        },
        {
          label: this.$t('NNTable.add_to_filter'),
          click: this.addToFilter,
          available: true
        },
        {
          label: this.$t('NNTable.hide_column'),
          click: this.hideColumn,
          available: true
        }
      ],
      timeout: null,
      toggleSelectAll: false
    }
  },
  methods: {
    getHeaderSlotName (header) {
      return `header.${header.value}`
    },
    getColumnInitialData (column) {
      return this.initialColumnData ? this.initialColumnData[column.value] : undefined
    },
    sortAscending (header) {
      this.options.sortBy[0] = header.value
      this.currentSortDirection = false
      this.filterTable()
    },
    sortDescending (header) {
      this.options.sortBy[0] = header.value
      this.currentSortDirection = true
      this.filterTable()
    },
    addToFilter (header) {
      if (this.itemsToFilter[this.itemsToFilter.findIndex(el => el.value === header.value)]) {
        this.itemsToFilter.splice(this.itemsToFilter.findIndex(el => el.value === header.value), 1)
      } else {
        this.itemsToFilter.push(header)
      }
      this.filterBarDisplay()
    },
    hideColumn (header) {
      this.shownColumns.splice(this.shownColumns.findIndex(el => el.value === header.value), 1)
      const layoutMap = new Map()
      layoutMap.set(this.$route.fullPath, this.shownColumns)
      this.$store.commit('tablesLayout/SET_COLUMNS', layoutMap)
    },
    rowClass () {
      return this.subTables ? 'subRowsTable' : ''
    },
    returnHasApi () {
      return this.hasApi
    },
    saveSelectedColumns (columns) {
      this.shownColumns = columns
      if (this.shownColumns.length === 0) {
        this.shownColumns = this.headers
      }
      this.headers.some(this.hasAction)
      const check = new Set()
      this.shownColumns = this.shownColumns.filter(obj => !check.has(obj.value) && check.add(obj.value))
    },
    hasAction (element) {
      if (element.value === 'actions' && !this.shownColumns.includes('actions')) {
        this.shownColumns.push(element)
      }
    },
    saveSelectedColumnsToFilter (columns) {
      if (columns.length === 0) {
        this.clearFilters()
        this.clearData()
      }
      this.itemsToFilter = columns
      this.filterBarDisplay()
    },
    filterBarDisplay () {
      this.itemsToFilter = this.itemsToFilter.filter(function (element) {
        return element !== undefined
      })
      this.showFilterBar = true
    },
    clearData () {
      if (this.hasApi) {
        this.clearFilters()
      }
      this.data = []
    },
    clearFilters () {
      this.apiParams.clear()
      this.trigger += 1
      this.$emit('filter')
    },
    fullTextSearch (value) {
      this.loading = true
      if (this.timeout) clearTimeout(this.timeout)
      this.timeout = setTimeout(() => {
        this.apiParams.set('*', [value])
        this.filterTable()
      }, 500)
    },
    columnFilter (params) {
      this.apiParams.set(params.column, params.data)
      this.filterTable()
    },
    filterTable (sort) {
      if (sort === undefined) {
        sort = this.currentSortDirection
      } else {
        sort = sort[0]
      }
      for (const elem of this.apiParams.entries()) {
        if (elem[1].length === 0) {
          this.apiParams.delete(elem[0])
        }
      }
      const newFilters = JSON.stringify(Object.fromEntries(this.apiParams)).replaceAll(':[', ' :{ "v": [').replaceAll(']}', ']}}').replaceAll('],', ']},')
      const filtersUpdated = (this.filters && newFilters !== this.filters)
      this.filters = newFilters
      let index = this.filters.indexOf('startDate')
      if (index === -1 && this.filters.indexOf('Timestamp') !== -1) {
        index = this.filters.indexOf('Timestamp')
      }
      if (index > -1) {
        this.filters = this.filters.substring(0, index + 46) + ', "op": "bw"' + this.filters.substring(index + 46)
      }
      this.$emit('filter', this.filters, sort, filtersUpdated)
      this.refreshFiltersTrigger += 1
    },
    async confirmExport (resolve) {
      if (!this.selected.length) {
        const msg = this.$t('NNTable.export_confirmation')
        if (!await this.$refs.confirm.open(msg, { type: 'warning' })) {
          resolve(false)
        }
      }
      resolve(true)
    }
  },
  watch: {
    headers (value) {
      this.shownColumns = value
    },
    items (val) {
      if (val) {
        this.loading = false
      }
    },
    showSelectBoxes (val) {
      if (!val) {
        this.selected = []
      }
    },
    showSelect () {
      this.showSelectBoxes = this.showSelect
    },
    itemsToFilter () {
      this.apiParams.forEach((value, key) => {
        const check = obj => obj.value === key
        if (!this.itemsToFilter.some(check)) {
          this.apiParams.delete(key)
        }
      })
      this.filterTable()
    }
  }
}
</script>

<style>
.disableUpperCase {
  text-transform: capitalize;
}
.headerRow {
  flex-wrap: unset;
}

.headerColor {
  background-color: rgba(0, 0, 0, 0.1);
  white-space: nowrap;
}
.upperRight {
  position: absolute;
  top: 50px;
  right: 0;
  border-radius: 0px;
}

.v-text-field .v-input__control .v-input__slot .v-text-field__slot {
  display: flex !important;
  min-height: 30px;
}

.v-text-field:not(.v-select--is-multi):not(.v-textarea--auto-grow) .v-input__control .v-input__slot {
  height: 30px !important;
}

.v-data-table-header tr {
  background-color: rgba(0, 0, 0, 0.1);
  white-space: nowrap;
}

.v-data-table-header th {
  white-space: inherit;
  min-width: 145px;
  vertical-align: text-top;
  padding-top: 20px !important;
  padding-bottom: 16px !important;
  padding-left: 28px !important;
  color: rgba(0, 0, 0, 0.6);
  text-align: start;
  font-weight: 500;
  font-size: 14px;
}

.autocomplete {
  width: auto !important;
  margin-top: 12px !important;
}

.autocomplete
.v-input__icon {
  margin-top: 2px !important;
}

.full.v-autocomplete.v-select.v-text-field input {
  max-width: fit-content;
}

.empty.v-autocomplete.v-select.v-text-field input {
  max-width: 100px;
}
.calendar
.v-text-field__slot{
  padding-right: 10px !important;
  margin-top: 5px;
}

.calendar {
  max-width: 180px;
  padding-top: 15px !important;
}

.subRowsTable {
  background-color: #E3F2FD;
}

.searchFieldLabel.v-text-field label {
  font-size: 14px;
}

</style>
