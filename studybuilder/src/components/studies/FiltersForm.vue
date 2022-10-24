<template>
<v-card color="white">
  <v-card-title>
    <span class="dialog-title">{{ title }}</span>
  </v-card-title>
  <v-card-text>
    <v-row no-gutters class="my-4">
      <v-col cols="6">
        <v-btn
          color="primary"
          @click="clearFilters"
          >
          {{ $t('FiltersForm.clear_all') }}
        </v-btn>
      </v-col>
    </v-row>
    <slot v-bind:form="form"></slot>
  </v-card-text>
  <v-card-actions class="pb-4">
    <v-spacer></v-spacer>
    <v-btn
      class="secondary-btn"
      color="white"
      @click="close"
      >
      {{ $t('_global.cancel') }}
    </v-btn>
    <v-btn
      color="secondary"
      @click="submit"
      :loading="loading"
      >
      {{ $t('_global.apply') }}
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
import i18n from '@/plugins/i18n'

export default {
  props: {
    title: {
      type: String,
      default: () => i18n.t('FiltersForm.title')
    }
  },
  data () {
    return {
      form: {},
      loading: false
    }
  },
  methods: {
    close () {
      this.$emit('close')
    },
    clearFilters () {
      this.form = {}
    },
    submit () {

    }
  }
}
</script>
