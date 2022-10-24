<template>
<v-radio-group
  :value="value"
  dense
  :key="radioKey"
  @change="update"
  v-bind="$attrs"
  v-on="$listeners"
  >
  <v-radio
    v-for="booleanValue in booleanValues"
    ref="radio"
    :data-cy="'radio-' + booleanValue.label"
    :key="booleanValue.id"
    :label="booleanValue.label"
    :value="booleanValue.value"
    @mouseup.native="clearCurrentRadioValue(booleanValue)"
    />
</v-radio-group>
</template>

<script>
export default {
  props: ['value'],
  data () {
    return {
      booleanValues: [
        { id: 1, label: this.$t('_global.yes'), value: true },
        { id: 2, label: this.$t('_global.no'), value: false }
      ],
      radioKey: 0
    }
  },
  methods: {
    clearCurrentRadioValue (value) {
      if (this.value !== null && value.value === this.value) {
        this.$emit('input', null)
        this.radioKey += 1
      }
    },
    update (value) {
      this.$emit('input', value)
    }
  }
}
</script>
