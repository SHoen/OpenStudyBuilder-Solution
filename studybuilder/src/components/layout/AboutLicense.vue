<template>
  <v-card color="dfltBackground">
    <v-card-actions>
      <v-card-title class="dialog-about-title">
        {{ this.title }}
    </v-card-title>
      <v-spacer></v-spacer>
      <v-btn class="secondary-btn" color="white" @click="$emit('close')">
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
    <v-card-text>
      <span v-html="this.licenseContent"></span>
    </v-card-text>
  </v-card>
</template>

<script>
import { marked } from 'marked'

export default {
  props: {
    rawMarkdown: String,
    title: String
  },
  computed: {
    licenseContent () {
      return marked.parse(this.rawMarkdown)
    }
  }
}
</script>
