<template>
<v-row>
  <v-col cols="6">
    <v-autocomplete
      :value="value"
      :label="$t('SubstanceField.label')"
      :items="substances"
      item-text="name"
      return-object
      @input="update"
      dense
      />
  </v-col>
  <v-col cols="6">
    <v-text-field
      :value="unii"
      label="UNII"
      filled
      disabled
      dense
      hide-details
      />
  </v-col>
  <v-col cols="6">
    <v-text-field
      :value="pclass"
      :label="$t('SubstanceField.pharmacological_class')"
      filled
      disabled
      dense
      hide-details
      />
  </v-col>
  <v-col cols="6">
    <v-text-field
      :value="medrtId"
      :label="$t('SubstanceField.medrt')"
      filled
      disabled
      dense
      hide-details
      />
  </v-col>
</v-row>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  props: {
    value: Object
  },
  computed: {
    ...mapGetters({
      substances: 'compounds/substances'
    })
  },
  data () {
    return {
      medrtId: '',
      pclass: '',
      unii: ''
    }
  },
  methods: {
    fillInformation (value) {
      if (value) {
        if (value.pclass) {
          this.pclass = value.pclass.name
          this.medrtId = value.pclass.dictionaryId
        } else {
          this.pclass = ''
          this.medrtId = ''
        }
        this.unii = value.dictionaryId
      }
    },
    update (val) {
      this.fillInformation(val)
      this.$emit('input', val)
    }
  },
  mounted () {
    if (this.value) {
      this.fillInformation(this.value)
    }
  },
  watch: {
    value: {
      handler: function (newValue) {
        this.fillInformation(newValue)
      },
      immediate: true
    },
    substances (value) {
      if (value) {
        this.fillInformation(this.value)
      }
    }
  }
}
</script>
