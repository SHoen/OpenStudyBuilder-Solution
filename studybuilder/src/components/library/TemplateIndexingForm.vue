<template>
<div>
  <not-applicable-field
    :clean-function="cleanIndications"
    :checked="template && (!template.indications || !template.indications.length)"
    >
    <template v-slot:mainField="{ notApplicable }">
      <validation-provider
        v-slot="{ errors }"
        :rules="`requiredIfNotNA:${notApplicable}`"
        >
        <multiple-select
          v-model="form.indications"
          :label="$t('GenericTemplateForm.study_indication')"
          data-cy="template-indication-dropdown"
          :items="indications"
          item-text="name"
          return-object
          :disabled="notApplicable"
          :errors="errors"
          />
      </validation-provider>
    </template>
  </not-applicable-field>
  <slot name="templateIndexFields"></slot>
</div>
</template>

<script>
import dictionaries from '@/api/dictionaries'
import MultipleSelect from '@/components/tools/MultipleSelect'
import NotApplicableField from '@/components/tools/NotApplicableField'

export default {
  components: {
    MultipleSelect,
    NotApplicableField
  },
  props: {
    form: Object,
    template: Object
  },
  data () {
    return {
      indications: []
    }
  },
  created () {
    dictionaries.getCodelists('SNOMED').then(resp => {
      /* FIXME: we need a direct way to retrieve the terms here */
      dictionaries.getTerms({ codelist_uid: resp.data.items[0].codelist_uid, page_size: 0 }).then(resp => {
        this.indications = resp.data.items
        this.indications.sort((a, b) => a.name.localeCompare(b.name))
      })
    })
  },
  methods: {
    cleanIndications (value) {
      if (value) {
        this.$set(this.form, 'indications', [])
      }
    }
  }
}
</script>
