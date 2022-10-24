<template>
<div>
  <v-row v-if="editMode">
    <v-select
      v-model="element"
      :items="studyElements"
      label="Element"
      item-text="name"
      item-value="elementUid"
      dense
      clearable
      class="mt-6 cellWidth"
      @input="updateElement"
      @click:clear="deleteElement"/>
  </v-row>
  <div v-else>
    <v-tooltip bottom>
      <template v-slot:activator="{ on, attrs }">
        <span
          v-bind="attrs"
          v-on="on">
          {{ getElementShortName(element) }}</span>
      </template>
        <span>{{ getElementName(element) }}</span>
    </v-tooltip>
  </div>
</div>
</template>
<script>
import { mapGetters } from 'vuex'

export default {
  components: {},
  props: {
    epoch: String,
    arm: String,
    armBranch: String,
    studyElements: Array,
    cells: Object,
    editMode: Boolean,
    saveObject: Boolean
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      element: '',
      cell: {},
      data: {}
    }
  },
  methods: {
    updateElement () {
      if (this.cell && this.element) {
        this.data = {
          method: 'PATCH',
          content: {
            studyElementUid: this.element,
            studyDesignCellUid: this.cell.designCellUid
          }
        }
        this.armBranch ? this.data.studyBranchArmUid = this.armBranch : this.data.studyArmUid = this.arm
      } else if (this.element) {
        this.data = {
          method: 'POST',
          content: {
            studyArmUid: this.arm,
            studyEpochUid: this.epoch,
            studyElementUid: this.element,
            studyBranchArmUid: this.armBranch
          }
        }
      }
    },
    deleteElement () {
      if (this.cell) {
        this.data = {
          method: 'DELETE',
          content: {
            uid: this.cell.designCellUid
          }
        }
        this.cell = undefined
      }
    },
    findCell (cell) {
      return (cell.studyEpochUid === this.epoch && (cell.studyArmUid ? (cell.studyArmUid === this.arm) : (cell.studyBranchArmUid === this.armBranch)))
    },
    getElementShortName (elementUid) {
      const element = this.studyElements.find(el => el.elementUid === elementUid)
      return element ? element.shortName : ''
    },
    getElementName (elementUid) {
      const element = this.studyElements.find(el => el.elementUid === elementUid)
      return element ? element.name : ''
    }
  },
  mounted () {
    this.cell = this.cells.data.find(this.findCell)
    if (this.cell) {
      this.element = this.cell.studyElementUid
    }
  },
  watch: {
    saveObject (value) {
      if (value) {
        this.$emit('addToObject', this.data)
      }
    }
  }

}
</script>
<style scoped>
  .cellWidth {
    max-width: 250px;
  }
</style>
