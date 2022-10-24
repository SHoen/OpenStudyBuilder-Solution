<template>
<v-app>
  <topbar @backToRoot="navigateToRoot" :hide-app-bar-nav-icon="layoutTemplate === 'empty'" />

  <template v-if="layoutTemplate === 'empty'">
    <v-main class="primary white--text">
      <router-view />
    </v-main>
  </template>

  <template v-else-if="layoutTemplate === 'error'">
    <v-main class="">
      <router-view />
    </v-main>
  </template>

  <template v-else>
    <sidebar />

    <v-main>
      <v-container class="" fluid>
        <v-breadcrumbs :items="breadcrumbs" class="mb-2" />
        <router-view />
      </v-container>
    </v-main>
  </template>

  <v-snackbar
    v-model="snackbar"
    :color="notificationColor"
    :timeout="notificationTimeout"
    :min-width="550"
    top
    centered
    tile
    >
    <v-row>
      <v-col cols="1">
        <v-icon class="mr-2" large>{{ notificationIcon }}</v-icon>
      </v-col>
      <v-col cols="10">
        <div class="text-body-1 mt-1">
          {{ notification }}
          <template v-if="correlationId">
            <p></p>
            <p class="text-body-2">
              <span class="font-weight-bold">{{ $t('_global.correlation_id') }}</span><br>
              {{ correlationId }}
            </p>
          </template>
        </div>
      </v-col>
      <v-col cols="1">
        <v-btn
          fab
          color="white"
          small
          icon
          @click="snackbar = false"
          >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </v-snackbar>
</v-app>
</template>
<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import Sidebar from './components/layout/Sidebar'
import Topbar from './components/layout/Topbar'

export default {
  name: 'App',

  components: {
    Sidebar,
    Topbar
  },

  /**
   * Register a callback to deal with global notifications.
   */
  created () {
    bus.$on('notification', this.showNotification)
    bus.$on('userSignedIn', () => {
      this.$store.dispatch('auth/initialize')
      this.$store.commit('auth/SET_WELCOME_MSG_FLAG', true)
    })
  },

  computed: {
    ...mapGetters({
      breadcrumbs: 'app/breadcrumbs',
      section: 'app/section',
      userData: 'app/userData',
      userInfo: 'auth/userInfo',
      displayWelcomeMsg: 'auth/displayWelcomeMsg'
    }),
    layoutTemplate () {
      return this.$route.meta.layoutTemplate || '2cols'
    },
    notificationIcon () {
      if (this.notificationColor === 'green' || this.notificationColor === 'success') {
        return 'mdi-check-circle'
      }
      if (this.notificationColor === 'info') {
        return 'mdi-information'
      }
      if (this.notificationColor === 'warning') {
        return 'mdi-alert'
      }
      if (this.notificationColor === 'error' || this.notificationColor === '#E6553F') {
        return 'mdi-alert-octagon'
      }
      return ''
    }
  },

  data: () => ({
    snackbar: false,
    correlationId: null,
    notification: '',
    notificationColor: null,
    notificationTimeout: -1,
    defaultNotificationTimeout: 3000
  }),

  methods: {
    navigateToRoot () {
      this.$store.commit('app/RESET_BREADCRUMBS')
      this.$store.commit('app/SET_SECTION', '')
      this.$router.push('/')
    },
    showNotification (options) {
      this.notification = options.msg
      if (options.type) {
        this.notificationColor = options.type === 'error' ? '#E6553F' : options.type
      } else {
        this.notificationColor = 'green'
      }
      this.notificationTimeout = (options.timeout) ? options.timeout : this.defaultNotificationTimeout
      this.correlationId = options.correlationId
      this.snackbar = true
      if (options.type === 'error') {
        console.log(options.msg)
        if (options.correlationId) {
          console.log(`Correlation ID: ${options.correlationId}`)
        }
      }
    }
  },

  mounted () {
    this.$store.dispatch('app/initialize')
    this.$vuetify.theme.dark = this.userData.darkTheme
    this.$store.dispatch('auth/initialize')
  },
  watch: {
    userInfo (newValue, oldValue) {
      if (this.displayWelcomeMsg) {
        this.showNotification({ msg: this.$t('_global.auth_success', { username: newValue.name }) })
        this.$store.commit('auth/SET_WELCOME_MSG_FLAG', false)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.v-breadcrumbs {
  padding-top: 5px;
  padding-bottom: 5px;
  padding-left: 12px;
}
.v-main {
  background-color: var(--v-dfltBackground-base);
}
</style>
