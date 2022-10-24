<template>
  <v-expansion-panels tile>
    <v-expansion-panel
      @change="expanded = !expanded">
      <v-expansion-panel-header v-if="!expanded && item.description.length > 30" class="pa-0 pl-2 pt-1">
        <p class="subtitle-1">{{ item.description.substring(0, 30) + '...' }}</p>
      </v-expansion-panel-header>
      <v-expansion-panel-header v-else class="pa-0 pl-2 pt-1">
        <p class="subtitle-1">{{ item.description }}</p>
      </v-expansion-panel-header>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script>

export default {
  props: ['item'],
  data () {
    return {
      expanded: false
    }
  }
}
</script>
