<template>
<div>
  <v-btn data-cy="help-button" icon color="primary" @click="showHelp = true">
    <v-icon>mdi-help-circle</v-icon>
  </v-btn>
  <v-dialog
    v-model="showHelp"
    width="495"
    persistent
    hide-overlay
    content-class="upperRight"
    class="rounded-0"
    >
    <v-card>
      <v-card-title class="dialog-title">{{ title }}
        <v-spacer></v-spacer>
        <v-btn
          color="secondary"
          @click="showHelp = false"
          icon
          >
        <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-text>
        <slot>
          {{ helpText }}
        </slot>
      </v-card-text>
    </v-card>
  </v-dialog>
</div>
</template>

<script>
export default {
  props: {
    helpText: String,
    title: {
      type: String,
      default: 'Online help'
    }
  },
  data () {
    return {
      showHelp: false
    }
  }
}
</script>
<style>
.upperRight {
  position: absolute;
  top: 50px;
  right: 0;
  border-radius: 0px;
}

</style>
