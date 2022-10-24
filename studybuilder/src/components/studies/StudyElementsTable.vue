<template>
<div>
  <n-n-table
    :headers="headers"
    :items="studyElements"
    :sort-desc="sortDesc"
    export-object-label="StudyElements"
    item-key="elementUid"
    :options.sync="options"
    :export-data-url="exportDataUrl"
    has-api
    :column-data-resource="`study/${selectedStudy.uid}/study-elements`"
    @filter="getStudyElements"
    >
    <template v-slot:afterSwitches>
      <div :title="$t('NNTableTooltips.reorder_content')">
        <v-switch
          v-model="sortMode"
          :label="$t('NNTable.reorder_content')"
          hide-details
          class="mr-6"
          />
      </div>
    </template>
    <template v-slot:body="props" v-if="sortMode">
      <draggable
        :list="props.items"
        tag="tbody"
        @change="onChange($event)"
        >
        <tr
          v-for="(item, index) in props.items"
          :key="index"
          >
          <td width="3%">
            <actions-menu :actions="actions" :item="item"/>
          </td>
          <td width="7%">
            <v-icon
              small
              class="page__grab-icon">
              mdi-sort
            </v-icon>
            {{ item.order }}
          </td>
          <td width="15%">{{ item.name }}</td>
          <td width="15%">{{ item.shortName }}</td>
          <td width="10%">{{ item.elementSubType.sponsorPreferredName }}</td>
          <td width="5%">{{ item.elementType }}</td>
          <td width="10%">{{ item.description }}</td>
          <td width="10%">{{ item.startDate | date }}</td>
          <td width="10%">{{ item.userInitials }}</td>
        </tr>
      </draggable>
    </template>
    <template v-slot:item.elementColour="{ item }">
      <v-chip :data-cy="'color='+item.elementColour" :color="item.elementColour" small />
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate | date }}
    </template>
    <template v-slot:item.actions="{ item }">
      <div class="pr-0 mr-0">
        <actions-menu :actions="actions" :item="item"/>
      </div>
    </template>
    <template v-slot:item.elementType="{ item }">
      {{ getElementType(item) }}
    </template>
    <template v-slot:actions="">
      <v-btn
        data-cy="add-study-compound"
        fab
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('StudyElements.add_element')"
      >
        <v-icon>
          mdi-plus
        </v-icon>
      </v-btn>
      <v-btn
        fab
        dark
        class="ml-2"
        small
        color="secondary"
        :title="$t('NNTableTooltips.history')"
        @click="openStudyElementsHistory()"
        >
        <v-icon dark>
          mdi-history
        </v-icon>
      </v-btn>
    </template>
  </n-n-table>
  <study-elements-form
    :open="showForm"
    @close="closeForm"
    :metadata="activeElement"
    />
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog v-model="showElementHistory">
    <history-table @close="closeElementHistory" :item="selectedElement" type="studyElement" :title-label="$t('StudyElements.study_element')"/>
  </v-dialog>
  <v-dialog v-model="showStudyElementsHistory">
    <summary-history-table @close="closeStudyElementsHistory" type="studyElements" :title-label="$t('StudyDesignTable.study_elements')" />
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import ActionsMenu from '@/components/tools/ActionsMenu'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import NNTable from '@/components/tools/NNTable'
import StudyElementsForm from './StudyElementsForm'
import arms from '@/api/arms'
import terms from '@/api/controlledTerminology/terms'
import draggable from 'vuedraggable'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/library/HistoryTable'
import SummaryHistoryTable from '@/components/tools/SummaryHistoryTable'

export default {
  components: {
    ConfirmDialog,
    NNTable,
    StudyElementsForm,
    ActionsMenu,
    draggable,
    HistoryTable,
    SummaryHistoryTable
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-elements`
    }
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editStudyElement
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteStudyElement
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openElementHistory
        }
      ],
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: '#', value: 'order', width: '5%' },
        { text: this.$t('StudyElements.el_type'), value: 'elementType' },
        { text: this.$t('StudyElements.el_sub_type'), value: 'elementSubType.sponsorPreferredName' },
        { text: this.$t('StudyElements.el_name'), value: 'name' },
        { text: this.$t('StudyElements.el_short_name'), value: 'shortName' },
        { text: this.$t('StudyElements.colour'), value: 'elementColour' },
        { text: this.$t('_global.description'), value: 'description' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: 'userInitials' }
      ],
      showForm: false,
      sortBy: 'name',
      sortDesc: false,
      studyElements: [],
      activeElement: null,
      elementTypes: [],
      sortMode: false,
      options: {},
      total: 0,
      showElementHistory: false,
      selectedElement: null,
      showStudyElementsHistory: false
    }
  },
  methods: {
    openStudyElementsHistory () {
      this.showStudyElementsHistory = true
    },
    closeStudyElementsHistory () {
      this.showStudyElementsHistory = false
    },
    getStudyElements (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.studyUid = this.selectedStudy.uid
      arms.getStudyElements(this.selectedStudy.uid, params).then(resp => {
        this.studyElements = resp.data.items
        this.total = resp.data.total
      })
    },
    async deleteStudyElement (element) {
      const options = { type: 'warning' }
      let msg
      const context = { element: element.name }
      if (element.studyCompoundDosingCount) {
        context.compoundDosings = element.studyCompoundDosingCount
        msg = this.$t('StudyElements.confirm_delete_cascade', context)
      } else {
        msg = this.$t('StudyElements.confirm_delete', context)
      }
      if (!await this.$refs.confirm.open(msg, options)) {
        return
      }
      arms.deleteStudyElement(this.selectedStudy.uid, element.elementUid).then(resp => {
        bus.$emit('notification', { msg: this.$t('StudyElements.el_deleted') })
        this.getStudyElements()
      })
    },
    editStudyElement (item) {
      this.activeElement = item
      this.showForm = true
    },
    closeForm () {
      this.activeElement = null
      this.showForm = false
      this.getStudyElements()
    },
    openElementHistory (item) {
      this.showElementHistory = true
      this.selectedElement = item
    },
    closeElementHistory (item) {
      this.showElementHistory = false
      this.selectedElement = null
    },
    getElementType (item) {
      const type = this.elementTypes.filter(el => el.termUid === item.code)[0]
      if (item.code && type) {
        return type.sponsorPreferredName
      }
    },
    onChange (event) {
      const element = event.moved.element
      const newOrder = {
        new_order: this.studyElements[event.moved.newIndex].order
      }
      arms.updateElementOrder(this.selectedStudy.uid, element.elementUid, newOrder).then(resp => {
        this.getStudyElements()
      })
    }
  },
  mounted () {
    this.getStudyElements()
    this.$store.dispatch('studiesGeneral/fetchUnits')
    terms.getByCodelist('elementTypes').then(resp => {
      this.elementTypes = resp.data.items
    })
  }
}
</script>
