<template>
<div>
  <n-n-table
    @filter="fetchStudyCohorts"
    :headers="headers"
    item-key=""
    :server-items-length="total"
    :options.sync="options"
    :items="cohorts">
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
        @click.stop="showForm()"
        title="Add Study Cohort"
        data-cy="add-study-cohort"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
      <v-btn
        fab
        dark
        small
        class="ml-2"
        color="secondary"
        :title="$t('NNTableTooltips.history')"
        @click="openStudyCohortsHistory()"
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
          <td width="5%">
            <v-icon
              small
              class="page__grab-icon">
              mdi-sort
            </v-icon>
            {{ item.order }}
          </td>
          <td width="10%">{{ item.armRoots|names }}</td>
          <td width="10%">{{ item.branchArmRoots|names }}</td>
          <td width="10%">{{ item.name }}</td>
          <td width="10%">{{ item.shortName }}</td>
          <td width="10%">{{ item.code }}</td>
          <td width="5%">{{ item.numberOfSubjects }}</td>
          <td width="10%">{{ item.description }}</td>
          <td width="10%"><v-chip :color="item.colourCode" small /></td>
          <td width="10%">{{ item.startDate | date }}</td>
          <td width="10%">{{ item.userInitials }}</td>
        </tr>
      </draggable>
    </template>
    <template v-slot:item.armRoots="{ item }">
      {{ item.armRoots|names }}
    </template>
    <template v-slot:item.branchArmRoots="{ item }">
      {{ item.branchArmRoots|names }}
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
  <study-cohorts-form
    :open="form"
    @close="closeForm"
    :editedCohort="cohortToEdit"
    :arms="arms"
    :branches="branches"/>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog v-model="showCohortHistory">
    <history-table @close="closeCohortHistory" :item="selectedCohort" type="studyCohort"  :title-label="$t('StudyCohorts.study_cohort')"/>
  </v-dialog>
  <v-dialog v-model="showStudyCohortsHistory">
    <summary-history-table @close="closeStudyCohortsHistory" type="studyCohorts" :title-label="$t('StudyDesignTable.study_cohorts')" />
  </v-dialog>
</div>
</template>

<script>

import NNTable from '@/components/tools/NNTable'
import arms from '@/api/arms'
import StudyCohortsForm from '@/components/studies/StudyCohortsForm'
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
    StudyCohortsForm,
    ActionsMenu,
    ConfirmDialog,
    draggable,
    HistoryTable,
    SummaryHistoryTable
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: '#', value: 'order', width: '5%' },
        { text: this.$t('StudyCohorts.arm_name'), value: 'armRoots' },
        { text: this.$t('StudyCohorts.branch_arm_name'), value: 'branchArmRoots' },
        { text: this.$t('StudyCohorts.cohort_name'), value: 'name' },
        { text: this.$t('StudyCohorts.cohort_short_name'), value: 'shortName' },
        { text: this.$t('StudyCohorts.cohort_code'), value: 'code' },
        { text: this.$t('StudyCohorts.number_of_subjects'), value: 'numberOfSubjects' },
        { text: this.$t('_global.description'), value: 'description' },
        { text: this.$t('StudyCohorts.colour'), value: 'colourCode' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.modified_by'), value: 'userInitials' }
      ],
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editCohort
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteCohort
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openCohortHistory
        }
      ],
      options: {},
      total: 0,
      cohorts: [],
      form: false,
      sortMode: false,
      arms: [],
      branches: [],
      cohortToEdit: {},
      showCohortHistory: false,
      selectedCohort: null,
      showStudyCohortsHistory: false
    }
  },
  mounted () {
    this.fetchStudyCohorts()
    this.fetchStudyArmsAndBranches()
  },
  methods: {
    openStudyCohortsHistory () {
      this.showStudyCohortsHistory = true
    },
    closeStudyCohortsHistory () {
      this.showStudyCohortsHistory = false
    },
    fetchStudyArmsAndBranches () {
      const params = {
        totalCount: true
      }
      arms.getAllForStudy(this.selectedStudy.uid, params).then(resp => {
        this.arms = resp.data.items
      })
      arms.getAllBranchArms(this.selectedStudy.uid, params).then(resp => {
        this.branches = resp.data
      })
    },
    fetchStudyCohorts () {
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      arms.getAllCohorts(this.selectedStudy.uid, params).then(resp => {
        this.cohorts = resp.data.items
        this.total = resp.data.total
      })
    },
    showForm () {
      this.form = true
    },
    closeForm () {
      this.form = false
      this.cohortToEdit = {}
      this.fetchStudyCohorts()
    },
    editCohort (item) {
      this.cohortToEdit = item
      this.form = true
    },
    openCohortHistory (item) {
      this.showCohortHistory = true
      this.selectedCohort = item
    },
    closeCohortHistory (item) {
      this.showCohortHistory = false
      this.selectedCohort = null
    },
    deleteCohort (item) {
      arms.deleteCohort(this.selectedStudy.uid, item.cohortUid).then(resp => {
        this.fetchStudyCohorts()
        bus.$emit('notification', { msg: this.$t('StudyCohorts.cohort_deleted') })
      })
    },
    onChange (event) {
      const cohort = event.moved.element
      const newOrder = {
        new_order: this.cohorts[event.moved.newIndex].order
      }
      arms.updateCohortOrder(this.selectedStudy.uid, cohort.cohortUid, newOrder).then(resp => {
        this.fetchStudyCohorts()
      })
    }
  },
  watch: {
    options () {
      this.fetchStudyCohorts()
    }
  }
}
</script>
