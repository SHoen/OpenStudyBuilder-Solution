<template>
<div>
  <n-n-table
    :headers="headers"
    :items="studyCompoundDosings"
    item-key="studyCompoundDosingUid"
    export-object-label="StudyCompoundDosings"
    :export-data-url="exportDataUrl"
    column-data-resource="study/study-compound-dosings"
    >
    <template v-slot:actions="">
      <v-btn
        data-cy="add-study-compound-dosing"
        fab
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('StudyCompoundForm.add_title')"
        >
        <v-icon>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.studyCompound.compoundAlias.isPreferredSynonym="{ item }">
      <template v-if="item.studyCompound.compoundAlias">
        {{ item.studyCompound.compoundAlias.isPreferredSynonym|yesno }}
      </template>
    </template>
    <template v-slot:item.doseValue="{ item }">
      <template v-if="item.doseValue">
        {{ item.doseValue.value }} {{ item.doseValue.unitLabel }}
      </template>
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
  </n-n-table>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog
    v-model="showForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
    >
    <compound-dosing-form
      @close="closeForm"
      :study-compound-dosing="selectedStudyCompoundDosing"
      />
  </v-dialog>
  <v-dialog
    v-model="showHistory"
    persistent
    max-width="1200px"
    >
    <history-table
      @close="closeHistory"
      type="studyCompoundDosing"
      :item="selectedStudyCompoundDosing"
      title-label="Study Compound Dosing"
      />
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import ActionsMenu from '@/components/tools/ActionsMenu'
import CompoundDosingForm from './CompoundDosingForm'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import HistoryTable from '@/components/library/HistoryTable'
import NNTable from '@/components/tools/NNTable'

export default {
  components: {
    ActionsMenu,
    CompoundDosingForm,
    ConfirmDialog,
    HistoryTable,
    NNTable
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyCompoundDosings: 'studyCompounds/studyCompoundDosings'
    }),
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-compound-dosings`
    }
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editStudyCompoundDosing
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteStudyCompoundDosing
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory
        }
      ],
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: '#', value: 'order' },
        { text: this.$t('StudyCompoundDosingTable.element'), value: 'studyElement.name' },
        { text: this.$t('StudyCompoundDosingTable.compound'), value: 'studyCompound.compound.name' },
        { text: this.$t('StudyCompoundDosingTable.compound_alias'), value: 'studyCompound.compoundAlias.name' },
        { text: this.$t('StudyCompoundDosingTable.preferred_alias'), value: 'studyCompound.compoundAlias.isPreferredSynonym' },
        { text: this.$t('StudyCompoundDosingTable.dose_value'), value: 'doseValue' },
        { text: this.$t('StudyCompoundDosingTable.dose_frequency'), value: 'doseFrequency.name' }
      ],
      selectedStudyCompoundDosing: null,
      showForm: false,
      showHistory: false
    }
  },
  methods: {
    async deleteStudyCompoundDosing (studyCompoundDosing) {
      const options = { type: 'warning' }
      const compound = studyCompoundDosing.studyCompound.compoundAlias.name
      const element = studyCompoundDosing.studyElement.name
      const msg = this.$t('StudyCompoundDosingTable.confirm_delete', { compound, element })
      if (!await this.$refs.confirm.open(msg, options)) {
        return
      }
      this.$store.dispatch('studyCompounds/deleteStudyCompoundDosing', {
        studyUid: this.selectedStudy.uid,
        studyCompoundDosingUid: studyCompoundDosing.studyCompoundDosingUid
      }).then(resp => {
        bus.$emit('notification', { msg: this.$t('StudyCompoundDosingTable.delete_success') })
      })
    },
    editStudyCompoundDosing (studyCompoundDosing) {
      this.selectedStudyCompoundDosing = studyCompoundDosing
      this.showForm = true
    },
    openHistory (studyCompoundDosing) {
      this.selectedStudyCompoundDosing = studyCompoundDosing
      this.showHistory = true
    },
    closeHistory () {
      this.selectedStudyCompoundDosing = null
      this.showHistory = false
    },
    closeForm () {
      this.showForm = false
      this.selectedStudyCompoundDosing = null
    }
  },
  mounted () {
    this.$store.dispatch('studyCompounds/fetchStudyCompoundDosings', this.selectedStudy.uid)
  }
}
</script>
