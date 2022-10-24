<template>
<div>
  <v-select
    :label="$t('NullFlavorSelect.label')"
    :value="value"
    :items="nullValues"
    item-text="sponsorPreferredName"
    item-value="termUid"
    return-object
    :error-messages="errors"
    @input="update"
    dense
    clearable
    data-cy="select-null-value"
    v-bind="$attrs"
    />
</div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  props: ['value', 'errors'],
  computed: {
    ...mapGetters({
      nullValues: 'studiesGeneral/nullValues'
    })
  },
  methods: {
    update (val) {
      const newValue = {
        termUid: val.termUid,
        name: val.sponsorPreferredName || val.name
      }
      this.$emit('input', newValue)
    }
  }
}
</script>
