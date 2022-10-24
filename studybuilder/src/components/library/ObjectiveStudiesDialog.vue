<template>
<v-card color="dfltBackground">
  <v-card-title>
    <span class="dialog-title">{{ $t('ObjectiveStudiesDialog.title') }}</span>
  </v-card-title>
  <v-card-text>
    <v-row class="mt-4">
      <v-col cols="2">
        <strong>{{ $t('ObjectiveStudiesDialog.objective_template') }}</strong>
      </v-col>
      <v-col cols="10">
        <n-n-parameter-highlighter :name="objective.objectiveTemplate.name" :show-prefix-and-postfix="false" />
      </v-col>
      <v-col cols="2">
        <strong>{{ $t('ObjectiveStudiesDialog.objective_text') }}</strong>
      </v-col>
      <v-col cols="10">
        <n-n-parameter-highlighter :name="objective.name" :show-prefix-and-postfix="false" />
      </v-col>
    </v-row>
    <n-n-table
      class="mt-4"
      :headers="headers"
      :items="studies"
      height="40vh"
      >
      <template v-slot:item.redirect="{ item }">
        <v-btn
          class="pb-3"
          fab
          dark
          small
          color="primary"
          @click="goToStudy(item)"
          icon
          >
          <v-icon dark>
            mdi-eye-arrow-right-outline
          </v-icon>
        </v-btn>
      </template>
      </n-n-table>
  </v-card-text>
  <v-card-actions>
    <v-spacer></v-spacer>
    <v-btn
      color="secondary"
      @click="close"
      >
      {{ $t('_global.close') }}
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
import objectives from '@/api/objectives'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter'
import NNTable from '@/components/tools/NNTable'

export default {
  components: {
    NNParameterHighlighter,
    NNTable
  },
  props: {
    objective: Object
  },
  data () {
    return {
      headers: [
        { text: this.$t('ObjectiveStudiesDialog.view'), value: 'redirect', width: '5%' },
        { text: this.$t('ObjectiveStudiesDialog.project_id'), value: 'currentMetadata.identificationMetadata.projectNumber' },
        { text: this.$t('ObjectiveStudiesDialog.project_name'), value: 'currentMetadata.identificationMetadata.projectName' },
        { text: this.$t('ObjectiveStudiesDialog.brand_name'), value: 'currentMetadata.identificationMetadata.brandName' },
        { text: this.$t('ObjectiveStudiesDialog.study_number'), value: 'studyNumber' },
        { text: this.$t('ObjectiveStudiesDialog.study_id'), value: 'studyId' },
        { text: this.$t('ObjectiveStudiesDialog.study_acronym'), value: 'studyAcronym' },
        { text: this.$t('_global.status'), value: 'studyStatus' }
      ],
      studies: []
    }
  },
  methods: {
    close () {
      this.$emit('close')
    },
    goToStudy (study) {
      this.$store.commit('studiesGeneral/SELECT_STUDY', study)
      this.$router.push({ name: 'StudyPurpose' })
    }
  },
  mounted () {
    objectives.getStudies(this.objective.uid).then(resp => {
      this.studies = resp.data
    })
  }
}
</script>
