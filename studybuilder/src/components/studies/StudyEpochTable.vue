<template>
<div>
  <n-n-table
    :headers="headers"
    :defaultHeaders="headers"
    :items="studyEpochs"
    item-key="uid"
    :options.sync="options"
    :export-data-url="exportDataUrl"
    @filter="fetchEpochs"
    has-api
    :column-data-resource="`study/${selectedStudy.uid}/study-epochs`"
    >
    <template v-slot:item.colorHash="{ item }">
      <v-chip :data-cy="'color='+item.colorHash" :color="item.colorHash" small />
    </template>
    <template v-slot:afterSwitches>
      <div :title="$t('NNTableTooltips.reorder_content')">
        <v-switch
          v-model="sortMode"
          :label="$t('NNTable.reorder_content')"
          hide-details
          class="mr-6"
          @change="switchSort"
          />
      </div>
    </template>
    <template v-slot:body="props" v-if="sortMode">
      <draggable
        :list="props.items"
        tag="tbody"
        @change="onOrderChange($event)"
        >
        <tr
          v-for="(item, index) in props.items"
          :key="index"
          >
          <td v-if="props.showSelectBoxes">
            <v-checkbox
              :value="item.uid"
              hide-details
              @change="props.select(!props.isSelected(item))"
              />
          </td>
          <td>
            <actions-menu :actions="actions" :item="item" />
          </td>
          <td></td>
          <td>
            <v-icon
              small
              class="page__grab-icon"
              >
              mdi-sort
            </v-icon>
            {{ item.order }}
          </td>
          <td>{{ item.epochName }}</td>
          <td>{{ getDisplay(item, 'epochType') }}</td>
          <td>{{ getDisplay(item, 'epochSubType') }}</td>
          <td>{{ item.startRule }}</td>
          <td>{{ item.endRule }}</td>
          <td>{{ item.description }}</td>
          <td>{{ item.studyVisitCount }}</td>
          <td><v-chip :data-cy="'color='+item.colorHash" :color="item.colorHash" small /></td>
        </tr>
      </draggable>
    </template>
    <template v-slot:item.epochType="{ item }">{{ getDisplay(item, 'epochType') }}</template>
    <template v-slot:item.epochSubType="{ item }">{{ getDisplay(item, 'epochSubType') }}</template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
    <template v-slot:actions="">
      <v-btn
        data-cy="create-epoch"
        fab
        dark
        small
        color="primary"
        @click="createEpoch()"
        :title="$t('StudyEpochForm.add_title')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
  </n-n-table>
  <study-epoch-form
  :open="showForm"
  :studyEpoch="selectedStudyEpoch"
  @close="closeForm" />
  <v-dialog v-model="showHistory">
    <history-table @close="closeHistory" type="studyEpoch" url-prefix="/studies/" :item="selectedStudyEpoch" :title-label="$t('StudyEpochTable.history_title')"/>
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import ActionsMenu from '@/components/tools/ActionsMenu'
import NNTable from '@/components/tools/NNTable'
import StudyEpochForm from './StudyEpochForm'
import terms from '@/api/controlledTerminology/terms'
import { bus } from '@/main'
import epochs from '@/api/studyEpochs'
import HistoryTable from '@/components/library/HistoryTable'
import draggable from 'vuedraggable'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    NNTable,
    StudyEpochForm,
    HistoryTable,
    draggable
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyEpochs: 'studyEpochs/studyEpochs'
    }),
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-epochs`
    }
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.possibleActions.find(action => action === 'edit'),
          click: this.editEpoch
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          condition: (item) => item.possibleActions.find(action => action === 'delete'),
          click: this.deleteEpoch
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openEpochHistory
        }
      ],
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyEpochTable.number'), value: 'order', width: '5%' },
        { text: this.$t('StudyEpochTable.name'), value: 'epochName' },
        { text: this.$t('StudyEpochTable.type'), value: 'epochType' },
        { text: this.$t('StudyEpochTable.sub_type'), value: 'epochSubType' },
        { text: this.$t('StudyEpochTable.start_rule'), value: 'startRule' },
        { text: this.$t('StudyEpochTable.end_rule'), value: 'endRule' },
        { text: this.$t('StudyEpochTable.description'), value: 'description', width: '20%' },
        { text: this.$t('StudyEpochTable.visit_count'), value: 'studyVisitCount' },
        { text: this.$t('StudyEpochTable.colour'), value: 'colorHash' }
      ],
      defaultColums: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyEpochTable.number'), value: 'order', width: '3%' },
        { text: this.$t('StudyEpochTable.name'), value: 'epochName' },
        { text: this.$t('StudyEpochTable.sub_type'), value: 'epochSubType' },
        { text: this.$t('StudyEpochTable.type'), value: 'epochType' },
        { text: this.$t('StudyEpochTable.start_rule'), value: 'startRule' },
        { text: this.$t('StudyEpochTable.end_rule'), value: 'endRule' },
        { text: this.$t('StudyEpochTable.description'), value: 'description' }
      ],
      selectedStudyEpoch: null,
      showForm: false,
      showHistory: false,
      componentKey: 0,
      calculatedItems: {},
      sortMode: false,
      selectMode: false,
      options: {},
      total: 0
    }
  },
  methods: {
    fetchEpochs (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.studyUid = this.selectedStudy.uid
      this.$store.dispatch('studyEpochs/fetchFilteredStudyEpochs', params)
    },
    switchSort () {
      if (this.selectMode && this.sortMode) {
        this.selectMode = false
      } else if (this.sortMode) {
        this.headers.unshift({ text: '', value: 'order', sortable: false, width: '5px' })
      } else {
        this.headers.shift()
      }
    },
    switchSelect () {
      if (this.sortMode && this.selectMode) {
        this.sortMode = false
      }
    },
    getDisplay (item, name) {
      if (name in this.calculatedItems) {
        return this.calculatedItems[name][item[name]]
      } else {
        return item[name]
      }
    },
    createMapping (codelist) {
      const returnValue = {}
      codelist.forEach(item => {
        returnValue[item.termUid] = item.sponsorPreferredName
      })
      return returnValue
    },
    editEpoch (item) {
      this.selectedStudyEpoch = item
      this.showForm = true
    },
    onOrderChange (event) {
      epochs.reorderStudyEpoch(this.selectedStudy.uid, this.studyEpochs[event.moved.oldIndex].uid, event.moved.newIndex).then(item => {
        this.$store.dispatch('studyEpochs/fetchStudyEpochs', this.selectedStudy.uid)
      })
    },
    createEpoch () {
      this.selectedStudyEpoch = null
      this.showForm = true
    },
    closeForm () {
      this.selectedStudyEpoch = null
      this.showForm = false
    },
    deleteEpoch (item) {
      if (item.studyVisitCount > 0) {
        const epoch = item.epochName
        bus.$emit('notification', { type: 'warning', msg: this.$t('StudyEpochTable.epoch_linked_to_visits_warning', { epoch }) })
        return
      }
      this.$store.dispatch('studyEpochs/deleteStudyEpoch', { studyUid: this.selectedStudy.uid, studyEpochUid: item.uid }).then(resp => {
        bus.$emit('notification', { msg: this.$t('StudyEpochTable.delete_success') })
      })
    },
    openEpochHistory (item) {
      this.selectedStudyEpoch = item
      this.showHistory = true
    },
    closeHistory () {
      this.selectedStudyEpoch = null
      this.showHistory = false
    }
  },
  mounted () {
    terms.getByCodelist('epochs').then(resp => {
      this.$set(this.calculatedItems, 'epoch', this.createMapping(resp.data.items))
    })
    terms.getByCodelist('epochTypes').then(resp => {
      this.$set(this.calculatedItems, 'epochType', this.createMapping(resp.data.items))
    })
    terms.getByCodelist('epochSubTypes').then(resp => {
      this.$set(this.calculatedItems, 'epochSubType', this.createMapping(resp.data.items))
    })
    this.$store.dispatch('studyEpochs/fetchStudyEpochs', this.selectedStudy.uid)
    this.$store.dispatch('studiesGeneral/fetchUnits')
    this.fetchEpochs()
  }
}
</script>
