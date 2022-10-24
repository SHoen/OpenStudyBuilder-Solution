<template>
<v-autocomplete
  multiple
  data-cy="autocomplete-input-field"
  :error-messages="errors"
  :item-text="itemText"
  :item-value="itemValue"
  :return-object="returnObject"
  @input="update"
  :search-input.sync="search"
  @change="search = ''"
  dense
  clearable
  hide-no-data
  v-bind="$attrs"
  v-on="$listeners"
  :value="value"
  >
  <template v-slot:selection="{index}" v-if="shorterPreview">
    <div v-if="index === 0">
      <span>{{ value[0].name.length > 10 ? value[0].name.substring(0, 10) + '...' : value[0].name }}</span>
    </div>
    <span
      v-if="index === 1"
      class="grey--text caption mr-1"
    >
      (+{{ value.length -1 }})
    </span>
  </template>
</v-autocomplete>
</template>

<script>
export default {
  props: {
    errors: Array,
    itemText: {
      type: String,
      default: 'name'
    },
    itemValue: {
      type: String,
      default: 'value'
    },
    returnObject: {
      type: Boolean,
      default: false
    },
    initialData: Array,
    shorterPreview: {
      type: Boolean,
      default: false
    },
    value: Array
  },
  data () {
    return {
      search: ''
    }
  },
  methods: {
    update (val) {
      this.$emit('input', val)
    }
  }
}
</script>
