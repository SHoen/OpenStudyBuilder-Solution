<template>
<div>
  <label v-if="label" class="v-label">{{ label }}</label>
  <v-row class="align-center pr-4">
    <v-col cols="11">
      <slot name="mainField" v-bind:notApplicable="notApplicable"></slot>
    </v-col>
    <v-col cols="1">
      <v-checkbox
        data-cy="not-applicable-checkbox"
        v-model="notApplicable"
        :label="naLabel"
        hide-details
        @change="cleanFunction"
        :disabled="disabled"
        />
    </v-col>
  </v-row>
</div>
</template>

<script>
import i18n from '@/plugins/i18n'

export default {
  props: {
    label: String,
    hint: String,
    naLabel: {
      type: String,
      default: () => i18n.t('_global.not_applicable')
    },
    cleanFunction: Function,
    checked: Boolean,
    disabled: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      notApplicable: false
    }
  },
  methods: {
    reset () {
      this.notApplicable = false
    }
  },
  created () {
    this.notApplicable = this.checked
  },
  watch: {
    checked (newValue) {
      this.notApplicable = this.checked
    }
  }
}
</script>
