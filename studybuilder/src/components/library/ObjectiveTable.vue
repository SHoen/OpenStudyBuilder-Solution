<template>
<div>
  <n-n-table
    :headers="headers"
    :items="objectives"
    item-key="uid"
    sort-by="startDate"
    export-object-label="Objectives"
    export-data-url="/objectives"
    sort-desc
    has-api
    @filter="fetchObjectives"
    column-data-resource="objectives"
    :options.sync="options"
    >
    <template v-slot:item.name="{ item }">
      <n-n-parameter-highlighter :name="item.name" :show-prefix-and-postfix="false" />
    </template>
    <template v-slot:item.objectiveTemplate.name="{ item }">
      <n-n-parameter-highlighter :name="item.objectiveTemplate.name" default-color="orange" />
    </template>
    <template v-slot:item.studyCount="{ item }">
      <v-chip small color="primary">{{ item.studyCount }}</v-chip>
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
  </n-n-table>
  <v-dialog v-model="showOHistory"
            persistent
            max-width="1200px">
    <history-table @close="closeHistory" type="objective" url-prefix="/endpoints/" :item="selectedObjective"
                   :title-label="$t('ObjectiveTable.singular_title')" />
  </v-dialog>
  <v-dialog v-model="showStudies"
            persistent
            max-width="1200px">
    <objective-studies-dialog :objective="selectedObjective" @close="closeObjectiveStudies" />
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import ActionsMenu from '@/components/tools/ActionsMenu'
import HistoryTable from '@/components/library/HistoryTable'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'
import ObjectiveStudiesDialog from './ObjectiveStudiesDialog'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    HistoryTable,
    NNParameterHighlighter,
    NNTable,
    ObjectiveStudiesDialog
  },
  computed: {
    ...mapGetters({
      objectives: 'objectives/objectives'
    })
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openObjectiveHistory
        },
        {
          label: this.$t('ObjectiveTable.show_studies'),
          icon: 'mdi-dots-horizontal-circle',
          click: this.showObjectiveStudies
        }
      ],
      headers: [
        {
          text: '',
          value: 'actions',
          sortable: false,
          width: '5%'
        },
        { text: this.$t('_global.library'), value: 'library.name' },
        { text: this.$t('_global.template'), value: 'objectiveTemplate.name', width: '30%' },
        { text: this.$t('_global.objective'), value: 'name' },
        { text: this.$t('ObjectiveTable.studies_count'), value: 'studyCount' }
      ],
      showStudies: false,
      showOHistory: false,
      selectedObjective: null,
      options: {}
    }
  },
  methods: {
    fetchObjectives (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      this.$store.dispatch('objectives/fetchFilteredObjectives', params)
    },
    closeHistory () {
      this.showOHistory = false
    },
    openObjectiveHistory (objective) {
      this.selectedObjective = objective
      this.showOHistory = true
    },
    showObjectiveStudies (objective) {
      this.selectedObjective = objective
      this.showStudies = true
    },
    closeObjectiveStudies () {
      this.showStudies = false
    }
  },
  mounted () {
    this.fetchObjectives()
  }
}
</script>
