<template>
<n-n-table
  key="studySelectionTable"
  :headers="headers"
  :items="studySelectionItems"
  hide-default-switches
  hide-actions-menu
  :items-per-page="15"
  elevation="0"
  :options.sync="options"
  :server-items-length="total"
  has-api
  @filter="getStudySelection"
  v-bind="$attrs"
  v-on="$listeners"
  >
  <template v-slot:item.studyUid="{ item }">
    {{ item.studyId }}
  </template>
  <template v-slot:item.actions="{ item }">
    <v-btn
      :data-cy="$t('StudySelectionTable.copy_item')"
      icon
      color="primary"
      @click="selectItem(item)"
      :title="$t('StudySelectionTable.copy_item')">
      <v-icon>mdi-content-copy</v-icon>
    </v-btn>
  </template>
  <template v-for="(_, slot) of $scopedSlots" v-slot:[slot]="scope">
    <slot :name="slot" v-bind="scope" />
  </template>
</n-n-table>
</template>

<script>
import { mapGetters } from 'vuex'
import NNTable from '@/components/tools/NNTable'
import study from '@/api/study'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    NNTable
  },
  props: {
    studies: Array,
    headers: Array,
    dataFetcherName: String,
    extraDataFetcherFilters: {
      type: Object,
      required: false
    }
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      options: {},
      studySelectionItems: [],
      total: 0
    }
  },
  mounted () {
    this.studySelectionItems = []
  },
  methods: {
    async getStudySelection (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      const studiesUids = []
      this.studies.forEach(el => {
        studiesUids.push(el.uid)
      })
      if (params.filters) {
        params.filters = JSON.parse(params.filters)
      } else {
        params.filters = {}
      }
      if (this.extraDataFetcherFilters) {
        Object.assign(params.filters, { ...this.extraDataFetcherFilters })
      }
      params.filters.studyUid = { v: studiesUids }
      study[this.dataFetcherName](params).then(resp => {
        this.studySelectionItems = resp.data.items
        this.studySelectionItems.forEach(el => {
          el.studyId = this.studies[this.studies.findIndex((study) => study.uid === el.studyUid)].studyId
        })
        this.total = resp.data.total
      })
    },
    selectItem (item) {
      this.$emit('item-selected', item)
    }
  },
  watch: {
    studies (value) {
      if (value && value.length) {
        this.getStudySelection()
      }
    }
  }
}
</script>
