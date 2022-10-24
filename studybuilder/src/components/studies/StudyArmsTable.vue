<template>
<div>
  <n-n-table
    @filter="fetchStudyArms"
    :headers="headers"
    item-key="uid"
    :server-items-length="total"
    :options.sync="options"
    :export-data-url="exportDataUrl"
    :items="arms"
    has-api
    :column-data-resource="`study/${selectedStudy.uid}/study-arms`"
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
          <td width="10%">{{ item.armType.sponsorPreferredName }}</td>
          <td width="10%">{{ item.name }}</td>
          <td width="10%">{{ item.shortName }}</td>
          <td width="10%">{{ item.randomizationGroup }}</td>
          <td width="5%">{{ item.code }}</td>
          <td width="5%">{{ item.numberOfSubjects }}</td>
          <td width="10%">{{ item.description }}</td>
          <td width="10%"><v-chip :color="item.armColour" small /></td>
          <td width="15%">{{ item.startDate | date }}</td>
          <td width="10%">{{ item.userInitials }}</td>
        </tr>
      </draggable>
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate|date }}
    </template>
    <template v-slot:item.armConnectedBranchArms="{ item }">
      {{ item.armConnectedBranchArms|names }}
    </template>
    <template v-slot:item.armColour="{ item }">
      <v-chip :color="item.armColour" small />
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
    <template v-slot:actions="">
      <v-btn
        fab
        dark
        small
        color="primary"
        @click.stop="showArmsForm = true"
        :title="$t('StudyArmsForm.add_arm')"
        data-cy="add-study-arm"
        >
        <v-icon dark>
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
        @click="openStudyArmsHistory()"
        >
        <v-icon dark>
          mdi-history
        </v-icon>
      </v-btn>
    </template>
  </n-n-table>
  <study-arms-form
    :open="showArmsForm"
    @close="closeForm"
    :editedArm="armToEdit"/>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog v-model="showArmHistory">
    <history-table @close="closeArmHistory" :item="selectedArm" type="studyArm" :title-label="$t('StudyArmsTable.study_arm')" />
  </v-dialog>
  <v-dialog v-model="showStudyArmsHistory">
    <summary-history-table @close="closeStudyArmsHistory" type="studyArms" :title-label="$t('StudyDesignTable.study_arms')" />
  </v-dialog>
</div>
</template>

<script>

import NNTable from '@/components/tools/NNTable'
import arms from '@/api/arms'
import StudyArmsForm from '@/components/studies/StudyArmsForm'
import { mapGetters } from 'vuex'
import ActionsMenu from '@/components/tools/ActionsMenu'
import { bus } from '@/main'
import draggable from 'vuedraggable'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import filteringParameters from '@/utils/filteringParameters'
import HistoryTable from '@/components/library/HistoryTable'
import SummaryHistoryTable from '@/components/tools/SummaryHistoryTable'

export default {
  components: {
    NNTable,
    StudyArmsForm,
    ActionsMenu,
    draggable,
    ConfirmDialog,
    HistoryTable,
    SummaryHistoryTable
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-arms`
    }
  },
  data () {
    return {
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: '#', value: 'order', width: '5%' },
        { text: this.$t('StudyArmsTable.type'), value: 'armType.sponsorPreferredName', width: '7%' },
        { text: this.$t('StudyArmsTable.name'), value: 'name' },
        { text: this.$t('StudyArmsTable.short_name'), value: 'shortName' },
        { text: this.$t('StudyArmsTable.randomisation_group'), value: 'randomizationGroup' },
        { text: this.$t('StudyArmsTable.code'), value: 'code' },
        { text: this.$t('StudyArmsTable.number_of_subjects'), value: 'numberOfSubjects' },
        { text: this.$t('StudyArmsTable.connected_branches'), value: 'armConnectedBranchArms' },
        { text: this.$t('StudyArmsTable.description'), value: 'description' },
        { text: this.$t('StudyBranchArms.colour'), value: 'armColour' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: 'userInitials' }
      ],
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editArm
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteArm
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openArmHistory
        }
      ],
      options: {},
      total: 0,
      arms: [],
      showArmsForm: false,
      armToEdit: {},
      sortMode: false,
      showArmHistory: false,
      selectedArm: null,
      showStudyArmsHistory: false
    }
  },
  methods: {
    openStudyArmsHistory () {
      this.showStudyArmsHistory = true
    },
    closeStudyArmsHistory () {
      this.showStudyArmsHistory = false
    },
    fetchStudyArms (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.studyUid = this.selectedStudy.uid
      arms.getAllForStudy(this.selectedStudy.uid, params).then(resp => {
        this.arms = resp.data.items
        this.total = resp.data.total
      })
    },
    closeForm () {
      this.armToEdit = {}
      this.showArmsForm = false
      this.fetchStudyArms()
    },
    editArm (item) {
      this.armToEdit = item
      this.showArmsForm = true
    },
    openArmHistory (item) {
      this.showArmHistory = true
      this.selectedArm = item
    },
    closeArmHistory (item) {
      this.showArmHistory = false
      this.selectedArm = null
    },
    async deleteArm (item) {
      let relatedItems = 0
      await arms.getAllBranchesForArm(this.selectedStudy.uid, item.armUid).then(resp => {
        relatedItems += resp.data.length
      })
      await arms.getAllCohortsForArm(this.selectedStudy.uid, item.armUid).then(resp => {
        relatedItems += resp.data.items.length
      })
      await arms.getAllCellsForArm(this.selectedStudy.uid, item.armUid).then(resp => {
        relatedItems += resp.data.length
      })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue')
      }
      if (relatedItems === 0) {
        arms.delete(this.selectedStudy.uid, item.armUid).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyArmsTable.arm_deleted') })
          this.fetchStudyArms()
        })
      } else if (await this.$refs.confirm.open(this.$t('StudyArmsTable.arm_delete_notification'), options)) {
        arms.delete(this.selectedStudy.uid, item.armUid).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyArmsTable.arm_deleted') })
          this.fetchStudyArms()
        })
      }
    },
    onChange (event) {
      const arm = event.moved.element
      const newOrder = {
        new_order: this.arms[event.moved.newIndex].order
      }
      arms.updateArmOrder(this.selectedStudy.uid, arm.armUid, newOrder).then(resp => {
        this.fetchStudyArms()
      })
    }
  },
  watch: {
    options () {
      this.fetchStudyArms()
    }
  }
}
</script>
