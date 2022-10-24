<template>
<simple-form-dialog
  ref="form"
  :title="$t('StudyVisitForm.duplicate_visit')"
  @close="close"
  @submit="submit"
  :open="open"
  max-width="400px"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <validation-provider
        v-slot="{ errors }"
        rules="required"
        >
        <v-text-field
          :label="$t('StudyVisitForm.time_value')"
          dense
          v-model="timing"
          :error-messages="errors"
          type="number"
        />
      </validation-provider>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import epochs from '@/api/studyEpochs'

export default {
  components: {
    SimpleFormDialog
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  props: {
    studyVisit: Object,
    open: Boolean
  },
  data () {
    return {
      timing: null,
      form: {}
    }
  },
  methods: {
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      try {
        this.$refs.form.working = true
        const newVisit = structuredClone(this.studyVisit)
        newVisit.timeValue = this.timing
        await epochs.getStudyVisitPreview(this.selectedStudy.uid, newVisit).then(resp => {
          for (const field of ['visitName', 'visitShortName', 'studyDayLabel', 'studyWeekLabel', 'studyDayNumber', 'studyWeekNumber', 'durationTime', 'uniqueVisitNumber', 'visitNumber']) {
            this.$set(newVisit, field, resp.data[field])
          }
          this.$store.dispatch('studyEpochs/addStudyVisit', { studyUid: this.selectedStudy.uid, input: newVisit }).then(resp => {
            this.$store.dispatch('studyEpochs/fetchStudyVisits', this.selectedStudy.uid)
          })
          bus.$emit('notification', { msg: this.$t('StudyVisitForm.visit_duplicated') })
          this.close()
        })
      } finally {
        this.$refs.form.working = false
      }
    },
    close () {
      this.timing = null
      this.$refs.observer.reset()
      this.$emit('close')
    }
  }
}
</script>
