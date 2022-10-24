<template>
<help-button>
  <v-expansion-panels
    v-bind="$attrs"
    >
    <v-expansion-panel v-if="helpText">
      <v-expansion-panel-header>
        {{ $t('_global.general_information') }}
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        {{ helpText }}
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel
      v-for="item in items"
      :key="item.key || item"
      >
      <v-expansion-panel-header>
        {{ getItemLabel(item) }}
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        {{ getItemHelp(item) }}
      </v-expansion-panel-content>
    </v-expansion-panel>
  </v-expansion-panels>
</help-button>
</template>

<script>
import HelpButton from './HelpButton'

export default {
  components: {
    HelpButton
  },
  props: {
    helpText: {
      type: String,
      required: false
    },
    items: Array
  },
  methods: {
    getItemLabel (item) {
      if (typeof item === 'string') {
        return this.$t(item)
      }
      return this.$t(item.key)
    },
    getItemHelp (item) {
      if (typeof item === 'string') {
        return this.$t(`_help.${item}`)
      }
      return this.$t(`_help.${item.key}`, item.context())
    }
  }
}
</script>
