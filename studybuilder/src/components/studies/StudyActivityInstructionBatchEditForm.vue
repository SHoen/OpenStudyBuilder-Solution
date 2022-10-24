<template>
<simple-form-dialog
  ref="form"
  :title="$t('StudyActivityInstructionBatchEditForm.title')"
  :help-items="helpItems"
  @close="close"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <v-autocomplete
      v-model="form.activityInstructionTemplate"
      :label="$t('StudyActivityInstructionBatchEditForm.select_template')"
      :items="templates"
      item-text="namePlain"
      return-object
      @change="loadParameters"
      />
    <validation-observer
      v-if="form.activityInstructionTemplate"
      ref="observer"
      >
      <v-progress-circular
        v-if="loadingParameters"
        indeterminate
        color="secondary"
        />
      <parameter-value-selector
        :value="parameters"
        :template="form.activityInstructionTemplate.name"
        color="white"
        />
    </validation-observer>
    <hr class="my-4 dfltBackground darken-1">
    <study-activity-selection-table
      :selection="selection"
      :title="$t('StudyActivityInstructionBatchForm.batch_table_title')"
      />
    <hr class="my-4 dfltBackground darken-1">
    <v-checkbox
      v-model="deleteSelection"
      :color="deleteSelection ? 'error': ''"
      >
      <template v-slot:label>
        <span :class="{ 'error--text': deleteSelection }">
          {{ $t('StudyActivityInstructionBatchEditForm.delete_selection') }}
        </span>
      </template>
    </v-checkbox>
  </template>
</simple-form-dialog>
</template>

<script>
import activityDescriptionTemplates from '@/api/activityDescriptionTemplates'
import { bus } from '@/main'
import instances from '@/utils/instances'
import { mapGetters } from 'vuex'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import study from '@/api/study'
import StudyActivitySelectionTable from './StudyActivitySelectionTable'

export default {
  components: {
    ParameterValueSelector,
    SimpleFormDialog,
    StudyActivitySelectionTable
  },
  props: {
    selection: Array,
    instructionsPerStudyActivity: Object,
    open: Boolean
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      deleteSelection: false,
      form: {},
      helpItems: [],
      loadingParameters: false,
      parameters: [],
      templates: []
    }
  },
  methods: {
    close () {
      this.$emit('close')
    },
    async loadParameters (template) {
      if (template) {
        this.loadingParameters = true
        const resp = await activityDescriptionTemplates.getObjectTemplateParameters(template.uid)
        this.parameters = resp.data
        this.loadingParameters = false
      } else {
        this.parameters = []
      }
    },
    async submit () {
      const operations = []
      let msg
      let notifType = 'success'
      let event

      this.$refs.form.working = true
      if (this.$refs.observer) {
        const isValid = await this.$refs.observer.validate()
        if (!isValid) {
          this.$refs.form.working = false
          return
        }
        for (const item of this.selection) {
          operations.push({
            method: 'DELETE',
            content: {
              studyActivityInstructionUid: this.instructionsPerStudyActivity[item.studyActivityUid].studyActivityInstructionUid
            }
          })
          operations.push({
            method: 'POST',
            content: {
              activityInstructionData: {
                activityInstructionTemplateUid: this.form.activityInstructionTemplate.uid,
                parameterValues: await instances.formatParameterValues(this.parameters),
                libraryName: this.form.activityInstructionTemplate.library.name
              },
              studyActivityUid: item.studyActivityUid
            }
          })
        }
        msg = this.$t('StudyActivityInstructionBatchEditForm.update_success')
        event = 'updated'
      } else if (this.deleteSelection) {
        for (const item of this.selection) {
          operations.push({
            method: 'DELETE',
            content: {
              studyActivityInstructionUid: this.instructionsPerStudyActivity[item.studyActivityUid].studyActivityInstructionUid
            }
          })
        }
        msg = this.$t('StudyActivityInstructionBatchEditForm.delete_success')
        event = 'deleted'
      }

      if (operations.length) {
        await study.studyActivityInstructionBatchOperations(this.selectedStudy.uid, operations)
        this.$emit(event)
      } else {
        notifType = 'info'
        msg = this.$t('_global.no_changes')
      }
      bus.$emit('notification', { msg, type: notifType })
      this.$refs.form.working = false
      this.close()
    },
    unselectItem (item) {
      this.$emit('remove', item)
    }
  },
  mounted () {
    const activityGroupUids = []
    const activitySubGroupUids = []
    for (const studyActivity of this.selection) {
      activityGroupUids.push(studyActivity.activity.activityGroup.uid)
      activitySubGroupUids.push(studyActivity.activity.activitySubGroup.uid)
    }
    const params = {
      filters: {
        'activityGroups.uid': { v: activityGroupUids },
        'activitySubGroups.uid': { v: activitySubGroupUids }
      },
      operator: 'or'
    }
    activityDescriptionTemplates.get(params).then(resp => {
      this.templates = resp.data.items
    })
  }
}
</script>
