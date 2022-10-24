<template>
<div>
  <div class="d-flex">
    <validation-observer ref="observer">
      <validation-provider
        v-slot="{ errors }"
        rules=""
        vid="manualInput"
        >
        <v-text-field
          class="value-selector"
          v-model="form.value"
          :label="label"
          type="number"
          hide-details="auto"
          :error-messages="errors"
          :disabled="disabled"
          dense
          @input="update"
          />
      </validation-provider>
    </validation-observer>
    <v-select
      class="unit-selector ml-4"
      v-model="form.unitDefinitionUid"
      :label="$t('DurationField.label')"
      :items="units"
      item-text="name"
      item-value="uid"
      dense
      clearable
      hide-details="auto"
      @input="update"
      :disabled="disabled"
      />
  </div>
  <div class="mt-1 v-messages theme--light">
    <div class="v-messages__message">
      {{ hint }}
    </div>
  </div>
</div>
</template>

<script>
import units from '@/api/units'

export default {
  props: {
    initialValue: Object,
    label: String,
    hint: String,
    subset: String,
    errors: Array,
    disabled: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      form: {},
      units: []
    }
  },
  methods: {
    update (val) {
      this.$emit('input', this.form)
    }
  },
  created () {
    this.form = { ...this.initialValue }
  },
  mounted () {
    units.getBySubset(this.subset).then(resp => {
      this.units = resp.data.items
    })
  },
  watch: {
    initialValue (val) {
      this.form = { ...val }
    }
  }
}
</script>

<style>
.value-selector {
  max-width: 100px;
}
.unit-selector {
  max-width: 200px;
}
</style>
