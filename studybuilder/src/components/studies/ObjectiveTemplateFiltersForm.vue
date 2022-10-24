<template>
<filters-form
  :title="$t('ObjectiveTemplateFiltersForm.title')"
  v-on="$listeners"
  >
  <template v-slot:default="{ form }">
    <label class="v-label">{{ $t('_global.library') }}</label>
    <multiple-select
      v-model="form.library"
      :items="libraries"
      item-text="name"
      return-object
      />
    <label class="v-label">{{ $t('ObjectiveTemplateFiltersForm.category') }}</label>
    <div class="d-flex">
      <multiple-select
        v-model="form.category"
        :items="categories"
        item-text="name"
        return-object
        />
      <v-radio-group
        class="ml-4"
        v-model="form.confirmatoryTesting"
        :label="$t('ObjectiveTemplateFiltersForm.confirmatory_testing')"
        >
        <v-radio :label="$t('_global.yes')" value="yes" />
        <v-radio :label="$t('_global.no')" value="no" />
        <v-radio :label="$t('_global.na')" value="na" />
      </v-radio-group>
    </div>
    <label class="v-label">{{ $t('ObjectiveTemplateFiltersForm.indication') }}</label>
    <multiple-select
      v-model="form.indication"
      :items="indications"
      item-text="name"
      return-object
      />
    <label class="v-label">{{ $t('ObjectiveTemplateFiltersForm.study_phase') }}</label>
    <multiple-select
      v-model="form.studyPhase"
      :items="studyPhases"
      item-text="sponsorPreferredName"
      return-object
      />

  </template>
</filters-form>
</template>

<script>
import dictionaries from '@/api/dictionaries'
import libraries from '@/api/libraries'
import terms from '@/api/controlledTerminology/terms'
import FiltersForm from './FiltersForm'
import MultipleSelect from '@/components/tools/MultipleSelect'

export default {
  components: {
    FiltersForm,
    MultipleSelect
  },
  data () {
    return {
      libraries: [],
      categories: [],
      indications: [],
      studyPhases: []
    }
  },
  mounted () {
    libraries.get().then(resp => {
      this.libraries = resp.data
    })
    dictionaries.getSnomedCategories().then(resp => {
      /* FIXME: we need a direct way to retrieve the terms here */
      resp.data.items.forEach(item => {
        if (item.name === 'Indications') {
          dictionaries.getTerms({ codelist_uid: item.codelistUid, pageSize: 40000 }).then(resp => {
            this.indications = resp.data.items
          })
        }
      })
    })
    terms.getByCodelist('trialPhase').then(resp => {
      this.studyPhases = resp.data.items
    })
  }
}
</script>
