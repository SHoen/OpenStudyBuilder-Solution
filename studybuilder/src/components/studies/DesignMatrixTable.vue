<template>
<div>
  <p class="grey--text text-subtitle-1 font-weight-bold ml-3">{{ $t('DesignMatrix.matrix_guide') }}</p>
  <n-n-table
    @filter="fetchStudyArms"
    :headers="headers"
    item-key="id"
    :server-items-length="total"
    :options.sync="options"
    disable-filtering
    :items="matrix"
    :loading="loading"
    hide-default-switches
    hide-export-button>
    <template v-slot:actions>
      <v-btn
        v-if="!editMode"
        fab
        small
        color="primary"
        @click.stop="edit"
        :title="$t('_global.edit')"
        >
        <v-icon dark>
          mdi-pencil
        </v-icon>
      </v-btn>
      <v-btn
        v-if="editMode"
        small
        color="primary"
        @click.stop="save"
        :title="$t('_global.save')"
        :loading="editLoading"
        >
        {{ $t('_global.save') }}
      </v-btn>
      <v-btn
        v-if="editMode"
        small
        class="secondary-btn ml-2"
        color="white"
        @click.stop="cancel"
        :title="$t('_global.cancel')"
        >
        {{ $t('_global.cancel') }}
      </v-btn>
    </template>
    <template v-for="header in headers" v-slot:[`item.${header.value}`]="item">
      <td v-bind:key="header.value">
        <elements-dropdown-list
          :saveObject="saveObject"
          v-bind:key="header.value"
          @addToObject="prepareUpdateObject"
          :editMode="editMode"
          :cells="cells"
          :study-elements="elements"
          :epoch="header.value"
          :arm="item.item.id ? null : item.item.uid "
          :armBranch="item.item.id" />
      </td>
    </template>
    <template v-slot:item.arms="item">
      <td>
        <v-chip v-if="item.item.armColor" small :color="item.item.armColor" class="mr-1"/>
        {{ item.value }}
      </td>
    </template>
    <template v-slot:item.branches="item">
      <td>
        <v-chip v-if="item.item.branchColor" small :color="item.item.branchColor" class="mr-1"/>
        {{ item.value }}
      </td>
    </template>
  </n-n-table>
</div>
</template>

<script>
import arms from '@/api/arms'
import { bus } from '@/main'
import ElementsDropdownList from '@/components/tools/ElementsDropdownList'
import { mapGetters } from 'vuex'
import NNTable from '@/components/tools/NNTable'
import visitConstants from '@/constants/visits'

export default {
  components: {
    NNTable,
    ElementsDropdownList
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyEpochs: 'studyEpochs/studyEpochs'
    }),
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-design-cells`
    },
    filteredStudyEpochs () {
      return this.studyEpochs.filter(item => item.epochName !== visitConstants.EPOCH_BASIC)
    }
  },
  props: {
    refresh: Number
  },
  data () {
    return {
      headers: [
        { text: this.$t('DesignMatrix.study_arm'), value: 'arms' },
        { text: this.$t('DesignMatrix.branches'), value: 'branches' }
      ],
      options: {},
      total: 0,
      arms: [],
      elements: [],
      cells: [],
      matrix: [],
      editMode: false,
      loading: true,
      updateObject: [],
      saveObject: false,
      editLoading: false
    }
  },
  methods: {
    async matrixPushCalls (matrixPushStack) {
      // this method is created to be sure that this.matrix is being pushed in the correct order, so the ElementsDropdownList won't have "Uncaught Promises"
      // we define the method as async
      // await for the sort to then await for each push in the correct order
      this.matrix = []
      // await for the sort
      await matrixPushStack.sort((a, b) => {
        return a.order - b.order
      })
      // await for each push in the correct order
      for (const iMatrix of matrixPushStack) {
        await this.matrix.push(iMatrix)
      }
    },
    async fetchStudyArms () {
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      let matrixPushStack = []
      arms.getAllForStudy(this.selectedStudy.uid, params).then(resp => {
        this.arms = resp.data.items
        this.total = resp.data.total
        this.matrix = []
        matrixPushStack = []
        for (let i = 0; i < this.arms.length; i++) {
          const el = this.arms[i]
          arms.getAllBranchesForArm(this.selectedStudy.uid, el.armUid).then(resp => {
            if (resp.data.length === 0) {
              // making a stack of what has to be pushed in this.matrix
              matrixPushStack.push({ uid: el.armUid, arms: el.name, armColor: el.armColour, order: el.order })
            } else {
              resp.data.forEach(value => {
                // making a stack of what has to be pushed in this.matrix
                matrixPushStack.push({ id: value.branchArmUid, uid: el.armUid, arms: el.name, armColor: value.armRoot.armColour, branches: value.name, branchColor: value.colourCode, order: el.order })
              })
            }
            // making this.matrix.push() in the right order
            this.matrixPushCalls(matrixPushStack)
          })
        }
        this.loading = false
      })
    },
    async fetchStudyElements () {
      return arms.getStudyElements(this.selectedStudy.uid).then(resp => {
        this.elements = resp.data.items
      })
    },
    edit () {
      this.editMode = true
    },
    save () {
      this.editLoading = true
      this.saveObject = true
      setTimeout(() => {
        this.updateObject = this.updateObject.filter(el => Object.keys(el).length !== 0)
        arms.cellsBatchUpdate(this.selectedStudy.uid, this.updateObject).then(resp => {
          this.editLoading = false
          this.editMode = false
          arms.getAllStudyCells(this.selectedStudy.uid).then(resp => {
            this.cells = resp
            bus.$emit('notification', { msg: this.$t('DesignMatrix.matrix_updated') })
            this.editLoading = false
            this.editMode = false
            this.updateObject = []
            this.saveObject = false
          })
        })
      }, 1000)
    },
    prepareUpdateObject (cell) {
      this.updateObject.push(cell)
    },
    cancel () {
      this.editMode = false
    }
  },
  async mounted () {
    this.$store.dispatch('studyEpochs/fetchStudyEpochs', this.selectedStudy.uid)
    await this.fetchStudyElements()
    await arms.getAllStudyCells(this.selectedStudy.uid).then(resp => {
      this.cells = resp
    })
  },
  watch: {
    studyEpochs () {
      this.headers = [
        { text: this.$t('DesignMatrix.study_arm'), value: 'arms' },
        { text: this.$t('DesignMatrix.branches'), value: 'branches' }
      ]
      this.filteredStudyEpochs.forEach(el => this.headers.push({ text: el.epochName, value: el.uid, color: el.colorHash }))
      this.fetchStudyArms()
    },
    refresh () {
      arms.getAllStudyCells(this.selectedStudy.uid).then(resp => {
        this.cells = resp
        this.fetchStudyArms()
        this.fetchStudyElements()
      })
    }
  }
}
</script>
<style scoped>
</style>
