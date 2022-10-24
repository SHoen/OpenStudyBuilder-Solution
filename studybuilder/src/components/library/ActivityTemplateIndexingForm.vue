<template>
<template-indexing-form
  :form="form"
  :template="template"
  >
  <template v-slot:templateIndexFields>
    <validation-provider
      v-slot="{ errors }"
      rules="required"
      >
      <v-row>
        <v-col cols="11">
          <v-autocomplete
            v-model="form.activityGroup"
            :label="$t('ActivityDescriptionTemplateForm.group')"
            :items="groups"
            item-text="name"
            item-value="uid"
            :error-messages="errors"
            dense
            clearable
            @change="setSubGroups"
            />
        </v-col>
      </v-row>
    </validation-provider>
    <validation-provider
      v-slot="{ errors }"
      rules="required"
      >
      <v-row>
        <v-col cols="11">
          <v-autocomplete
            v-model="form.activitySubGroups"
            :label="$t('ActivityDescriptionTemplateForm.sub_group')"
            :items="subGroups"
            item-text="name"
            item-value="uid"
            :error-messages="errors"
            dense
            clearable
            multiple
            @change="setActivities"
            />
        </v-col>
      </v-row>
    </validation-provider>
    <not-applicable-field
      :checked="template && !template.activities"
      :clean-function="value => $set(form, 'activities', null)"
      >
      <template v-slot:mainField="{ notApplicable }">
        <validation-provider
          v-slot="{ errors }"
          name="activity"
          :rules="`requiredIfNotNA:${notApplicable}`"
          >
          <v-row>
            <v-col cols="11">
              <v-select
                v-model="form.activities"
                :label="$t('ActivityDescriptionTemplateForm.activity')"
                :items="activities"
                item-text="name"
                return-object
                :error-messages="errors"
                dense
                clearable
                multiple
                :disabled="notApplicable"
                />
            </v-col>
          </v-row>
        </validation-provider>
      </template>
    </not-applicable-field>
  </template>
</template-indexing-form>
</template>

<script>
import activities from '@/api/activities'
import NotApplicableField from '@/components/tools/NotApplicableField'
import TemplateIndexingForm from './TemplateIndexingForm'

export default {
  components: {
    NotApplicableField,
    TemplateIndexingForm
  },
  props: {
    form: Object,
    template: Object
  },
  data () {
    return {
      activities: [],
      groups: [],
      subGroups: []
    }
  },
  methods: {
    preparePayload (form) {
      const result = {}
      result.activityGroupUids = [form.activityGroup]
      result.activitySubGroupUids = []
      for (const item of form.activitySubGroups) {
        const itemUid = (typeof item !== 'string') ? item.uid : item
        result.activitySubGroupUids.push(itemUid)
      }
      if (form.activities) {
        result.activityUids = form.activities.map(item => item.uid)
      }
      return result
    },
    async setSubGroups (group, noSubgroupReset) {
      if (group) {
        const resp = await activities.getSubGroups(group)
        this.subGroups = resp.data.items
      }
      if (!noSubgroupReset) {
        this.$set(this.form, 'activitySubGroups', [])
      }
    },
    setActivities (subgroup) {
      if (subgroup.length) {
        activities.getSubGroupActivities(subgroup[0].uid).then(resp => {
          this.activities = resp.data.items
        })
      }
    }
  },
  created () {
    activities.getGroups().then(resp => {
      this.groups = resp.data.items
    })
  },
  watch: {
    template: {
      handler: async function (value) {
        if (value && value.activityGroups && value.activityGroups.length) {
          const activityGroupUid = (typeof this.template.activityGroups[0] !== 'string')
            ? this.template.activityGroups[0].uid
            : this.template.activityGroups[0]
          this.$set(this.form, 'activityGroup', activityGroupUid)
          await this.setSubGroups(this.form.activityGroup, true)
          if (!this.form.activitySubGroups) {
            this.$set(this.form, 'activitySubGroups', value.activitySubGroups)
          }
        }
      },
      immediate: true
    }
  }
}
</script>
