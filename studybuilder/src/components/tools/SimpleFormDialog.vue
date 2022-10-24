<template>
<div>
  <v-dialog
    v-model="open"
    scrollable
    persistent
    :max-width="maxWidth">
    <v-card data-cy="form-body" elevation="0">
      <v-card-title>
        <span>{{ title }}</span>
        <help-button-with-panels
          :title="$t('_global.help')"
          :help-text="helpText"
          :items="helpItems"
          />
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <div>
          <slot name="body"></slot>
        </div>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          data-cy="cancel-button"
          class="secondary-btn"
          color="white"
          @click="cancel"
          >
          {{ $t('_global.cancel') }}
        </v-btn>
        <v-btn
          data-cy="save-button"
          color="secondary"
          @click="submit"
          :loading="working"
          >
          {{ $t('_global.save') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'

export default {
  components: {
    ConfirmDialog,
    HelpButtonWithPanels
  },
  props: {
    title: String,
    helpItems: Array,
    helpText: {
      type: String,
      required: false
    },
    open: Boolean,
    maxWidth: {
      type: String,
      default: '800px'
    }
  },
  data () {
    return {
      working: false
    }
  },
  methods: {
    cancel () {
      this.$emit('close')
    },
    async confirm (message, options) {
      return await this.$refs.confirm.open(message, options)
    },
    submit () {
      this.$emit('submit')
    }
  }
}
</script>
