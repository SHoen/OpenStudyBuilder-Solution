<template>
<v-dialog
  v-model="dialog"
  :max-width="options.width"
  :style="{ zIndex: options.zIndex }"
  @keydown.esc="cancel"
  >
  <v-card :color="backgroundColor">
    <v-card-text
      v-if="message"
      class="pt-2 white--text"
      >
      <v-row no-gutters class="align-center pa-2">
        <v-col cols="2" >
          <v-icon class="mr-4" color="white" x-large>{{ icon }}</v-icon>
        </v-col>
        <v-col cols="10">
          <div class="text-body-1 mt-1">
             {{ message }}
          </div>
        </v-col>
      </v-row>
      <v-divider class="pa-2" />
      <v-row>
        <v-col class="text-center">
          <v-btn
            v-if="!options.noCancel"
            color="white"
            @click.native="cancel"
            outlined
            class="mr-2"
            elevation="2"
            >
            {{ options.cancelLabel }}
          </v-btn>
          <slot name="actions">
            <v-btn
              v-if="!options.noAgree && options.redirect === ''"
              color="white"
              @click.native="agree"
              outlined
              elevation="2"
              >
              {{ options.agreeLabel }}
            </v-btn>
            <v-btn
              v-else
              color="white"
              @click.native="agreeAndRedirect"
              outlined
              elevation="2"
              >
              {{ options.agreeLabel }}
            </v-btn>
          </slot>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</v-dialog>
</template>

<script>
export default {
  computed: {
    backgroundColor () {
      if (this.options.type === 'warning') {
        return 'warning'
      }
      if (this.options.type === 'info') {
        return 'info'
      }
      return 'green'
    },
    icon () {
      if (this.options.type === 'info') {
        return 'mdi-information'
      }
      if (this.options.type === 'warning') {
        return 'mdi-alert'
      }
      if (this.options.type === 'error') {
        return 'mdi-alert-octagon'
      }
      return 'mdi-check-circle'
    }
  },
  data () {
    return {
      dialog: false,
      resolve: null,
      reject: null,
      message: null,
      type: null,
      options: {
        type: 'success',
        width: 450,
        zIndex: 200,
        noCancel: false,
        noAgree: false,
        agreeLabel: this.$t('_global.continue'),
        cancelLabel: this.$t('_global.cancel'),
        cancelIsPrimaryAction: false,
        redirect: ''
      }
    }
  },
  methods: {
    open (message, options) {
      this.dialog = true
      this.message = message
      this.options = Object.assign(this.options, options)
      return new Promise((resolve, reject) => {
        this.resolve = resolve
        this.reject = reject
      })
    },
    agree () {
      this.resolve(true)
      this.dialog = false
    },
    agreeAndRedirect () {
      this.dialog = false
      this.$router.push({ path: this.options.redirect })
      window.location.reload()
    },
    cancel () {
      this.resolve(false)
      this.dialog = false
    }
  }
}
</script>
