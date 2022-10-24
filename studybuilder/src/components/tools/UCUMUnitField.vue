<template>
<div>
  <v-autocomplete
    :label="$t('UCUMUnitField.label')"
    :value="value"
    :items="ucumUnits"
    :item-text="getUcumDisplay"
    return-object
    dense
    clearable
    @update:search-input="searchForUnit"
    v-bind="$attrs"
    v-on="$listeners"
    @change="update"
    />
</div>
</template>

<script>
import * as ucumlhc from '@lhncbc/ucum-lhc'

const utils = ucumlhc.UcumLhcUtils.getInstance()

export default {
  props: ['value'],
  data () {
    return {
      ucumUnits: []
    }
  },
  methods: {
    searchForUnit (value) {
      const result = utils.checkSynonyms(value)
      if (result.status === 'succeeded') {
        this.ucumUnits = result.units
      }
    },
    getUcumDisplay (item) {
      return `${item.code} (${item.name})`
    },
    update (value) {
      this.$emit('input', value)
    }
  }

}
</script>
