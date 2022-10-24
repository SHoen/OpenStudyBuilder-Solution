<template>
<simple-form-dialog
  ref="form"
  :title="title"
  :help-items="helpItems"
  @close="close"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            name="Project"
            vid="project"
            rules="required"
            >
            <v-select
              v-model="form.projectNumber"
              :label="$t('StudyForm.project_id')"
              :items="projects"
              item-text="projectNumber"
              @change="updateProject($event)"
              return-object
              :error-messages="errors"
              dense
              clearable
              data-cy="project-id"
              ></v-select>
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-text-field
            :label="$t('StudyForm.project_name')"
            :value="project.name"
            disabled
            filled
            hide-details
            data-cy="project-name"
            ></v-text-field>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-text-field
            :label="$t('StudyForm.brand_name')"
            :value="project.brandName"
            disabled
            filled
            hide-details
            data-cy="brand-name"
            ></v-text-field>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            name="Number"
            :rules="`numeric|max:${userData.studyNumberLength}`"
            >
            <v-text-field
              id="studyNumber"
              :label="$t('StudyForm.number')"
              v-model="form.studyNumber"
              :error-messages="errors"
              dense
              clearable
              data-cy="study-number"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            name="Acronym"
            rules=""
            >
            <v-text-field
              id="studyAcronym"
              :label="$t('StudyForm.acronym')"
              v-model="form.studyAcronym"
              :error-messages="errors"
              dense
              clearable
              data-cy="study-acronym"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-text-field
            :label="$t('StudyForm.study_id')"
            :value="studyId"
            disabled
            filled
            hide-details
            data-cy="study-id"
            />
        </v-col>
      </v-row>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import _isEqual from 'lodash/isEqual'
import _isEmpty from 'lodash/isEmpty'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'

export default {
  components: {
    SimpleFormDialog
  },
  props: {
    editedStudy: Object,
    open: Boolean
  },
  data () {
    return {
      form: {},
      helpItems: [
        'StudyForm.project_id',
        'StudyForm.project_name',
        'StudyForm.brand_name',
        'StudyForm.study_id',
        { key: 'StudyForm.number', context: this.getNumberTranslationContext },
        'StudyForm.acronym'
      ],
      project: {}
    }
  },
  computed: {
    ...mapGetters({
      getProjectByNumber: 'manageStudies/getProjectByNumber',
      projects: 'manageStudies/projects',
      selectedStudy: 'studiesGeneral/selectedStudy',
      userData: 'app/userData'
    }),
    title () {
      return (this.editedStudy) ? this.$t('StudyForm.edit_title') : this.$t('StudyForm.add_title')
    },
    studyId () {
      if (this.project.projectNumber && this.form.studyNumber) {
        return `${this.project.projectNumber}-${this.form.studyNumber}`
      }
      return ''
    }
  },
  methods: {
    async close () {
      if (this.hasChanged()) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue')
        }
        if (await this.$refs.form.confirm(this.$t('_global.cancel_changes'), options)) {
          this.form = {}
          this.project = {}
          this.$emit('close')
        }
      } else {
        this.form = {}
        this.project = {}
        this.$emit('close')
      }
    },
    initForm (value) {
      this.form = {
        projectNumber: value.currentMetadata.identificationMetadata.projectNumber,
        studyNumber: value.currentMetadata.identificationMetadata.studyNumber,
        studyAcronym: value.currentMetadata.identificationMetadata.studyAcronym
      }
      this.project = this.getProjectByNumber(this.form.projectNumber)
    },
    updateProject (target) {
      this.project = target
    },
    addStudy () {
      const data = JSON.parse(JSON.stringify(this.form))
      data.projectNumber = this.project.projectNumber
      return this.$store.dispatch('manageStudies/addStudy', data).then(resp => {
        bus.$emit('notification', { msg: this.$t('StudyForm.add_success') })
        this.$store.commit('studiesGeneral/SELECT_STUDY', resp.data)
        this.$router.push({ name: 'SelectOrAddStudy' })
      })
    },
    hasChanged () {
      if ((!_isEmpty(this.form) && this.editedStudy === null) || (!_isEmpty(this.form) && (this.editedStudy && (!_isEqual(this.form.projectNumber, this.editedStudy.projectNumber) || !_isEqual(this.form.studyAcronym, this.editedStudy.studyAcronym) || !_isEqual(this.form.studyNumber, this.editedStudy.studyNumber))))) {
        return true
      } else {
        return false
      }
    },
    updateStudy () {
      if (!this.hasChanged()) {
        bus.$emit('notification', { msg: this.$t('_global.no_changes'), type: 'info' })
        return
      }
      const data = JSON.parse(JSON.stringify(this.form))
      data.projectNumber = this.project.projectNumber
      return this.$store.dispatch('manageStudies/editStudyIdentification', [this.editedStudy.uid, data]).then(resp => {
        if (this.selectedStudy && (this.editedStudy.uid === this.selectedStudy.uid)) {
          this.$store.commit('studiesGeneral/SELECT_STUDY', resp.data)
        }
        bus.$emit('notification', { msg: this.$t('StudyForm.update_success') })
      })
    },
    getNumberTranslationContext () {
      return { length: this.userData.studyNumberLength }
    },
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.$refs.form.working = true
      try {
        if (!this.editedStudy) {
          await this.addStudy()
        } else {
          await this.updateStudy()
        }
        this.form = {}
        this.project = {}
        this.$emit('close')
      } finally {
        this.$refs.form.working = false
      }
    }
  },
  mounted () {
    if (this.editedStudy) {
      this.initForm(this.editedStudy)
    }
    this.$store.dispatch('manageStudies/fetchProjects')
    this.$store.dispatch('manageStudies/fetchStudies')
  },
  watch: {
    editedStudy: {
      handler (value) {
        if (value) {
          this.initForm(value)
        }
      },
      immediate: true
    }
  }
}
</script>
