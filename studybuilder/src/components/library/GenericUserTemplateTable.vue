<template>
<n-n-table
  v-model="selected"
  :headers="headers"
  :items="templates"
  item-key="uid"
  :export-object-label="objectType"
  :export-data-url="urlPrefix"
  :server-items-length="total"
  sort-by="startDate"
  sort-desc
  :options.sync="options"
  :has-api="hasApi"
  :column-data-resource="columnDataResource"
  @filter="filter"
  >
  <template v-for="(_, slot) of $scopedSlots" v-slot:[slot]="scope">
    <slot :name="slot" v-bind="scope" />
  </template>
  <template v-slot:item.name="{ item }">
    <n-n-parameter-highlighter :name="item.name" default-color="orange" />
  </template>
  <template v-slot:item.startDate="{ item }">
    {{ item.startDate | date }}
  </template>
  <template v-slot:item.status="{ item }">
    <status-chip :status="item.status" />
  </template>
</n-n-table>
</template>

<script>
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import templates from '@/api/templates'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    NNParameterHighlighter,
    NNTable
  },
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
    }
  },
  data () {
    return {
      headers: [
        { text: this.$t('_global.template'), value: 'name', width: '70%' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: 'fixme' }
      ],
      options: {},
      selected: [],
      templates: [],
      total: 0,
      api: null
    }
  },
  created () {
    this.api = templates(this.urlPrefix)
  },
  methods: {
    async filter (filters, sort, filtersUpdated) {
      filters = (filters) ? JSON.parse(filters) : {}
      filters['library.name'] = { v: ['User Defined'] }
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
}
</script>
