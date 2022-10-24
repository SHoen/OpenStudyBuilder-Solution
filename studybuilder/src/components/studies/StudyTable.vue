<template>
<div>
  <n-n-table
    :headers="headers"
    :items="studies.items"
    item-key="uid"
    export-object-label="Studies"
    export-data-url="studies"
    :options.sync="options"
    has-api
    column-data-resource="studies"
    @filter="fetchStudies"
    :server-items-length="total"
    has-history
    >
    <template v-slot:actions="">
      <v-btn
        data-cy="add-study"
        fab
        dark
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('StudyForm.add_title')"
        >
        <v-icon dark>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.brandName="{ item }">
      {{ getBrandName(item) }}
    </template>
    <template v-slot:item.currentMetadata.versionMetadata.versionTimestamp="{ item }">
      {{ item.currentMetadata.versionMetadata.versionTimestamp | date }}
    </template>
    <template v-slot:item.currentMetadata.versionMetadata.lockedVersionAuthor>
      {{ $t('_global.unknown_user') }}
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
  </n-n-table>
  <study-form
  :open="showForm"
  @close="closeForm"
  :edited-study="activeStudy"/>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import ActionsMenu from '@/components/tools/ActionsMenu'
import NNTable from '@/components/tools/NNTable'
import StudyForm from '@/components/studies/StudyForm'
import study from '@/api/study'
import constants from '@/constants/study'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    NNTable,
    StudyForm
  },
  computed: {
    ...mapGetters({
      getProjectByNumber: 'manageStudies/getProjectByNumber',
      selectedStudy: 'studiesGeneral/selectedStudy',
      studies: 'manageStudies/studies'
    })
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('StudyTable.select'),
          icon: 'mdi-check-circle-outline',
          iconColor: 'primary',
          condition: (item) => !this.selectedStudy || this.selectedStudy.uid !== item.uid,
          click: this.selectStudy
        },
        {
          label: this.$t('StudyTable.unselect'),
          icon: 'mdi-check-circle',
          iconColor: 'green',
          condition: (item) => this.selectedStudy && this.selectedStudy.uid === item.uid,
          click: this.unSelectStudy
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          condition: (item) => item.studyStatus === 'DRAFT',
          click: this.editStudy
        }
      ],
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: this.$t('StudyTable.clinical_programme'), value: 'currentMetadata.identificationMetadata.clinicalProgrammeName' },
        { text: this.$t('StudyTable.project_id'), value: 'currentMetadata.identificationMetadata.projectNumber' },
        { text: this.$t('StudyTable.project_name'), value: 'currentMetadata.identificationMetadata.projectName' },
        { text: this.$t('StudyTable.brand_name'), value: 'brandName' },
        { text: this.$t('StudyTable.number'), value: 'currentMetadata.identificationMetadata.studyNumber' },
        { text: this.$t('StudyTable.id'), value: 'currentMetadata.identificationMetadata.studyId' },
        { text: this.$t('StudyTable.acronym'), value: 'currentMetadata.identificationMetadata.studyAcronym' },
        { text: this.$t('StudyTable.title'), value: 'currentMetadata.studyDescription.studyTitle' },
        { text: this.$t('_global.status'), value: 'currentMetadata.versionMetadata.studyStatus' },
        { text: this.$t('_global.modified'), value: 'currentMetadata.versionMetadata.versionTimestamp' },
        { text: this.$t('_global.modified_by'), value: 'currentMetadata.versionMetadata.lockedVersionAuthor' }
      ],
      showForm: false,
      activeStudy: null,
      total: 0,
      filters: '',
      options: {}
    }
  },
  methods: {
    fetchStudies (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.fields = `${constants.IDENTIFICATION_METADATA}, ${constants.VERSION_METADATA}, ${constants.DESCRIPTION_METADATA}`
      study.get(params).then(resp => {
        this.studies.items = resp.data.items
        this.total = resp.data.total
      })
    },
    closeForm () {
      this.showForm = false
      this.activeStudy = null
    },
    selectStudy (study) {
      this.$store.commit('studiesGeneral/SELECT_STUDY', study)
    },
    unSelectStudy (study) {
      this.$store.commit('studiesGeneral/UNSELECT_STUDY', study)
    },
    editStudy (study) {
      this.activeStudy = study
      this.showForm = true
    },
    getBrandName (study) {
      const project = this.getProjectByNumber(study.currentMetadata.identificationMetadata.projectNumber)
      return (project !== undefined) ? project.brandName : ''
    },
    initialSortByDate () {
      this.options.sortBy = ['currentMetadata.versionMetadata.versionTimestamp']
      this.options.sortDesc = [true]
    }
  },
  mounted () {
    this.$store.dispatch('manageStudies/fetchProjects')
    this.$store.dispatch('manageStudies/fetchStudies')
    this.initialSortByDate()
  },
  watch: {
    options () {
      this.fetchStudies()
    }
  }
}
</script>
