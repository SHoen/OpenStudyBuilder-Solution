<template>
<v-card color="dfltBackground">
  <v-card-title>
    <span class="dialog-title">{{ $t('StudyActivityEditForm.title') }}</span>
    <help-button-with-panels :title="$t('_global.help')" :items="helpItems" />
  </v-card-title>
  <v-card-text class="mt-4">
    <div class="white pa-4">
      <div class="d-flex">
        <v-text-field
          :label="$t('StudyActivity.activity_group')"
          :value="activityGroup"
          disabled
          filled
          class="mr-2"
          />
        <v-text-field
          :label="$t('StudyActivity.activity_sub_group')"
          :value="activitySubGroup"
          disabled
          filled
          class="mr-2"
          />
        <v-text-field
          :label="$t('StudyActivity.activity')"
          :value="activity"
          disabled
          filled
          />
      </div>
      <validation-observer ref="observer">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-autocomplete
            v-model="form.flowchartGroup"
            :label="$t('StudyActivityForm.flowchart_group')"
            :items="flowchartGroups"
            item-text="sponsorPreferredName"
            return-object
            :error-messages="errors"
            clearable
            />
        </validation-provider>
      </validation-observer>
      <v-textarea
        v-model="form.note"
        :label="$t('StudyActivity.footnote')"
        rows="1"
        clearable
        auto-grow
        />
    </div>
  </v-card-text>
  <v-card-actions class="pr-6 pb-6">
    <v-spacer></v-spacer>
    <v-btn
      class="secondary-btn"
      color="white"
      @click="close"
      >
      {{ $t('_global.cancel') }}
    </v-btn>
    <v-btn
      color="secondary"
      :loading="working"
      @click="submit"
      >
      {{ $t('_global.save') }}
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
import { bus } from '@/main'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'

export default {
  props: ['studyActivity'],
  components: {
    HelpButtonWithPanels
  },
  computed: {
    activityGroup () {
      return (this.studyActivity && this.studyActivity.activity)
        ? this.studyActivity.activity.activityGroup.name
        : ''
    },
    activitySubGroup () {
      return (this.studyActivity && this.studyActivity.activity)
        ? this.studyActivity.activity.activitySubGroup.name
        : ''
    },
    activity () {
      return (this.studyActivity) ? this.studyActivity.activity.name : ''
    }
  },
  data () {
    return {
      flowchartGroups: [],
      form: {},
      helpItems: [],
      working: false
    }
  },
  methods: {
    close () {
      this.working = false
      this.form = {}
      this.$refs.observer.reset()
      this.$emit('close')
    },
    cancel () {
      this.close()
    },
    async submit () {
      const valid = this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.working = true
      const data = {
        flowchartGroupUid: this.form.flowchartGroup.termUid,
        note: this.form.note
      }
      study.updateStudyActivity(this.studyActivity.studyUid, this.studyActivity.studyActivityUid, data).then(resp => {
        bus.$emit('notification', { type: 'success', msg: this.$t('StudyActivityEditForm.update_success') })
        this.$emit('updated')
        this.close()
      })
    }
  },
  mounted () {
    terms.getByCodelist('flowchartGroups').then(resp => {
      this.flowchartGroups = resp.data.items
    })
  },
  watch: {
    studyActivity: {
      handler (value) {
        this.form = (value) ? { ...value } : {}
      },
      immediate: true
    }
  }
}
</script>
