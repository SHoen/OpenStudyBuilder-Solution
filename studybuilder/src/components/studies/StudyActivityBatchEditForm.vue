<template>
<study-activity-selection-base-form
  :help-items="helpItems"
  :selection="selection"
  @submit="submit"
  @close="close"
  with-delete-action
  @remove="unselectItem"
  :open="open"
  >
  <template v-slot:body>
    <v-autocomplete
      v-model="form.flowchartGroup"
      :label="$t('StudyActivityForm.flowchart_group')"
      :items="flowchartGroups"
      item-text="sponsorPreferredName"
      return-object
      clearable
      class="border-top mt-4"
      />
    <v-textarea
      v-model="form.note"
      :label="$t('StudyActivity.footnote')"
      rows="1"
      clearable
      auto-grow
      />
    <v-checkbox
      v-model="form.deleteSelection"
      :color="form.deleteSelection ? 'error': ''"
      >
      <template v-slot:label>
        <span :class="{ 'error--text': form.deleteSelection }">
          {{ $t('StudyActivityBatchEditForm.delete_selection') }}
        </span>
      </template>
    </v-checkbox>
  </template>
</study-activity-selection-base-form>
</template>

<script>
import { bus } from '@/main'
import { mapGetters } from 'vuex'
import study from '@/api/study'
import StudyActivitySelectionBaseForm from './StudyActivitySelectionBaseForm'
import terms from '@/api/controlledTerminology/terms'

export default {
  components: {
    StudyActivitySelectionBaseForm
  },
  props: {
    selection: Array,
    open: Boolean
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      flowchartGroups: [],
      form: {},
      helpItems: []
    }
  },
  methods: {
    close () {
      this.form = {}
      this.$emit('close')
    },
    unselectItem (item) {
      this.$emit('remove', item)
    },
    async submit () {
      const data = []
      if (this.form.deleteSelection) {
        for (const item of this.selection) {
          data.push({
            method: 'DELETE',
            content: {
              studyActivityUid: item.studyActivityUid
            }
          })
        }
      }
      if (this.form.flowchartGroup || this.form.note) {
        const data = []
        for (const item of this.selection) {
          data.push({
            method: 'PATCH',
            content: {
              studyActivityUid: item.studyActivityUid,
              content: {
                flowchartGroupUid: this.form.flowchartGroup.termUid,
                note: this.form.note
              }
            }
          })
        }
      }
      if (data.length) {
        study.studyActivityBatchOperations(this.selectedStudy.uid, data).then(resp => {
          bus.$emit('notification', { type: 'success', msg: this.$t('StudyActivityBatchEditForm.update_success') })
          this.$emit('updated')
          this.close()
        })
      } else {
        this.close()
      }
    }
  },
  mounted () {
    terms.getByCodelist('flowchartGroups').then(resp => {
      this.flowchartGroups = resp.data.items
    })
  }
}
</script>

<style scoped>
.border-top {
  border-top: 1px solid var(--v-dfltBackground-darken1);
}
</style>
