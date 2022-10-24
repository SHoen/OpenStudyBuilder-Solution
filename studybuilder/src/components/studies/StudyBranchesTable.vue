<template>
<div>
  <n-n-table
    @filter="fetchStudyBranchArms"
    :headers="headers"
    item-key="branchArmUid"
    :server-items-length="total"
    :options.sync="options"
    :items="branchArms"
    :no-data-text="arms.length === 0 ? $t('StudyBranchArms.no_data') : undefined"
    :export-data-url="exportDataUrl"
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
    <template v-slot:actions="">
      <v-btn
        fab
        dark
        small
        color="primary"
        @click.stop="addBranchArm"
        :title="$t('StudyBranchArms.add_branch')"
        data-cy="add-study-branch-arm"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
      <v-btn
        fab
        class="ml-2"
        dark
        small
        color="secondary"
        :title="$t('NNTableTooltips.history')"
        @click="openStudyBranchesHistory()"
        >
        <v-icon dark>
          mdi-history
        </v-icon>
      </v-btn>
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
          <td width="15%">{{ item.armRoot.name }}</td>
          <td width="15%">{{ item.name }}</td>
          <td width="15%">{{ item.shortName }}</td>
          <td width="10%">{{ item.randomizationGroup }}</td>
          <td width="10%">{{ item.code }}</td>
          <td width="5%">{{ item.numberOfSubjects }}</td>
          <td width="10%">{{ item.description }}</td>
          <td width="10%"><v-chip :color="item.colourCode" small /></td>
          <td width="10%">{{ item.startDate | date }}</td>
          <td width="10%">{{ item.userInitials }}</td>
        </tr>
      </draggable>
    </template>
    <template v-slot:item.colourCode="{ item }">
      <v-chip :data-cy="'color='+item.colourCode" :color="item.colourCode" small />
    </template>
    <template v-slot:item.startDate="{ item }">
      {{ item.startDate|date }}
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
  </n-n-table>
  <study-branches-form
    :open="showBranchArmsForm"
    @close="closeForm"
    :editedBranchArm="branchArmToEdit"
    :arms="arms"/>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog v-model="showBranchHistory">
    <history-table @close="closeBranchHistory" :item="selectedBranch" type="studyBranch" :title-label="$t('StudyBranchArms.study_branch_arm')"/>
  </v-dialog>
  <v-dialog v-model="showStudyBranchesHistory">
    <summary-history-table @close="closeStudyBranchesHistory" type="studyBranches" :title-label="$t('StudyDesignTable.study_branches')" />
  </v-dialog>
</div>
</template>

<script>

import NNTable from '@/components/tools/NNTable'
import arms from '@/api/arms'
import StudyBranchesForm from '@/components/studies/StudyBranchesForm'
import { mapGetters } from 'vuex'
import ActionsMenu from '@/components/tools/ActionsMenu'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import { bus } from '@/main'
import draggable from 'vuedraggable'
import HistoryTable from '@/components/library/HistoryTable'
import SummaryHistoryTable from '@/components/tools/SummaryHistoryTable'

export default {
  components: {
    NNTable,
    StudyBranchesForm,
    ActionsMenu,
    ConfirmDialog,
    draggable,
    HistoryTable,
    SummaryHistoryTable
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-branch-arms`
    }
  },
  data () {
    return {
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: '#', value: 'order', width: '5%' },
        { text: this.$t('StudyBranchArms.arm_name'), value: 'armRoot.name' },
        { text: this.$t('StudyBranchArms.name'), value: 'name' },
        { text: this.$t('StudyBranchArms.short_name'), value: 'shortName' },
        { text: this.$t('StudyBranchArms.randomisation_group'), value: 'randomizationGroup' },
        { text: this.$t('StudyBranchArms.code'), value: 'code' },
        { text: this.$t('StudyBranchArms.number_of_subjects'), value: 'numberOfSubjects' },
        { text: this.$t('StudyBranchArms.description'), value: 'description' },
        { text: this.$t('StudyBranchArms.colour'), value: 'colourCode' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: 'userInitials' }
      ],
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editBranchArm
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteBranchArm
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openBranchHistory
        }
      ],
      options: {},
      total: 0,
      arms: [],
      showBranchArmsForm: false,
      branchArmToEdit: {},
      branchArms: [],
      sortMode: false,
      showBranchHistory: false,
      selectedBranch: null,
      showStudyBranchesHistory: false
    }
  },
  mounted () {
    this.fetchStudyArms()
  },
  methods: {
    openStudyBranchesHistory () {
      this.showStudyBranchesHistory = true
    },
    closeStudyBranchesHistory () {
      this.showStudyBranchesHistory = false
    },
    fetchStudyArms () {
      const params = {
        totalCount: true
      }
      arms.getAllForStudy(this.selectedStudy.uid, params).then(resp => {
        this.arms = resp.data.items
      })
    },
    fetchStudyBranchArms () {
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      arms.getAllBranchArms(this.selectedStudy.uid, params).then(resp => {
        this.branchArms = resp.data
        this.total = resp.data.total
      })
    },
    closeForm () {
      this.branchArmToEdit = {}
      this.showBranchArmsForm = false
      this.fetchStudyBranchArms()
    },
    editBranchArm (item) {
      this.branchArmToEdit = item
      this.showBranchArmsForm = true
    },
    openBranchHistory (item) {
      this.showBranchHistory = true
      this.selectedBranch = item
    },
    closeBranchHistory (item) {
      this.showBranchHistory = false
      this.selectedBranch = null
    },
    async deleteBranchArm (item) {
      let cellsInBranch = 0
      await arms.getAllCellsForBranch(this.selectedStudy.uid, item.branchArmUid).then(resp => {
        cellsInBranch = resp.data.length
      })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue')
      }
      if (cellsInBranch === 0) {
        arms.deleteBranchArm(this.selectedStudy.uid, item.branchArmUid).then(resp => {
          this.fetchStudyBranchArms()
          bus.$emit('notification', { msg: this.$t('StudyBranchArms.branch_deleted') })
        })
      } else if (await this.$refs.confirm.open(this.$t('StudyBranchArms.branch_delete_notification'), options)) {
        arms.deleteBranchArm(this.selectedStudy.uid, item.branchArmUid).then(resp => {
          this.fetchStudyBranchArms()
          bus.$emit('notification', { msg: this.$t('StudyBranchArms.branch_deleted') })
        })
      }
    },
    async addBranchArm () {
      this.fetchStudyArms()
      if (this.arms.length === 0) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('StudyBranchArms.add_arm'),
          redirect: 'arms'
        }
        if (!await this.$refs.confirm.open(this.$t('StudyBranchArms.add_arm_message'), options)) {
          return
        }
      }
      this.showBranchArmsForm = true
    },
    onChange (event) {
      const branch = event.moved.element
      const newOrder = {
        new_order: this.branchArms[event.moved.newIndex].order
      }
      arms.updateBranchArmOrder(this.selectedStudy.uid, branch.branchArmUid, newOrder).then(resp => {
        this.fetchStudyBranchArms()
      })
    }
  },
  watch: {
    options () {
      this.fetchStudyBranchArms()
    }
  }
}
</script>
