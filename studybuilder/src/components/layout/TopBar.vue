<template>
<v-app-bar
  color="primary"
  elevation="2"
  dark
  app
  clipped-left
  height="70"
  >
  <v-app-bar-nav-icon data-cy="topbar-menu-button" v-if="!hideAppBarNavIcon" @click="drawer = !drawer" elevation="6"></v-app-bar-nav-icon>
  <div data-cy="topbar-logo" class="d-flex action" @click="navigateToRoot">
    <v-img
      class="mx-6"
      src="../../assets/study_builder_homepage_logo.png"
      contain
      transition="scale-transition"
      width="190"
      />
  </div>

  <v-toolbar-items class="hidden-xs-only">
    <v-btn v-for="app in availableApps"
           :data-cy="app.name"
           class="text-capitalize"
           :key="app.name"
           :to="{ name: app.name }"
           text
           >
      <v-icon>{{ app.icon }}</v-icon>
      {{ app.name }}
    </v-btn>
  </v-toolbar-items>
  <v-spacer />
  <div v-if="isAuthenticated">
    <v-btn
      class="text-capitalize"
      data-cy="topbar-select-study"
      @click="openSelectStudyDialog"
      text>
      {{ $t('Topbar.select_study') }}
    </v-btn>
    <v-chip
      v-if="selectedStudy"
      data-cy="topbar-selected-study"
      class="ma-2"
      :color="currentStudyStatus === 'DRAFT' ? 'green' : currentStudyStatus === 'LOCKED' ? 'red' : 'blue'"
      >
      {{ selectedStudy.current_metadata.identification_metadata.study_id || selectedStudy.current_metadata.identification_metadata.study_acronym }}
      <v-icon
        right
        small
        v-if="currentStudyStatus === 'DRAFT'"
      >
        mdi-lock-open-outline
      </v-icon>
      <v-icon
        right
        small
        v-else>
        mdi-lock-outline
      </v-icon>
    </v-chip>
    <v-chip
      v-if="selectedStudy && this.selectedStudyVersion"
      :color="currentStudyStatus === 'DRAFT' ? 'green' : currentStudyStatus === 'LOCKED' ? 'red' : 'blue'"
      >
      v{{ selectedStudy && this.selectedStudyVersion }}
    </v-chip>
  </div>
  <v-btn data-cy="topbar-admin-icon" icon :title="$t('Topbar.admin')" @click="openSettingsBox">
    <v-icon>mdi-cog-outline</v-icon>
  </v-btn>
  <v-menu offset-y v-if="isAuthenticated">
    <template v-slot:activator="{ on, attrs }">
      <v-btn data-cy="topbar-help" icon :title="$t('Topbar.help')" v-bind="attrs" v-on="on">
        <v-icon>mdi-help-circle-outline</v-icon>
      </v-btn>
    </template>
    <v-list dense>
      <v-list-item data-cy="topbar-documentation-portal" :href="documentationPortalUrl" target="_blank">
        <v-list-item-icon>
          <v-icon>mdi-book-open-outline</v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>{{ $t('Topbar.documentation_portal') }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-list-item data-cy="topbar-user-guide" :href="helpUrl" target="_blank">
        <v-list-item-icon>
          <v-icon>mdi-book-open-outline</v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>{{ $t('Topbar.user_guide') }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-list-item data-cy="topbar-about" @click="openAboutBox">
        <v-list-item-icon>
          <v-icon>mdi-information-outline</v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>{{ $t('Topbar.about') }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </v-menu>
  <v-menu offset-y v-if="isAuthenticated">
    <template v-slot:activator="{ on, attrs }">
      <v-btn
        data-cy="topbar-user-name"
        id="user-menu-btn"
        class="ma-2 white--text"
        text
        v-bind="attrs"
        v-on="on"
        >
        <v-icon
          right
          class="mx-2"
          >
          mdi-account-outline
        </v-icon>
        {{ username }}
      </v-btn>
    </template>
    <v-list dense>
      <v-list-item v-if="userInfo">
        <v-list-item-icon>
          <v-icon>mdi-security</v-icon>
        </v-list-item-icon>
        <v-list-item-content style="max-width: 200px;">
          <v-list-item-title>{{ $t('_global.access_groups') }}</v-list-item-title>
          <v-list-item-subtitle v-for="(role, index) of userInfo.roles" v-bind:key="index">{{role}}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
      <v-list-item :to="{ name: 'Logout' }" data-cy="topbar-logout">
        <v-list-item-icon>
          <v-icon>mdi-export</v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>{{ $t('_global.logout') }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </v-menu>
  <v-btn
    data-cy="topbar-login"
    v-else
    id="login-btn"
    class="text-capitalize mr-4"
    :to="{ name: 'Login' }"
    text
    >
    <v-icon>mdi-login</v-icon>
    {{ $t('_global.login') }}
  </v-btn>
  <div class="d-flex">
    <v-img
      class="mr-4"
      src="../../assets/nn_logo_rgb_white_small.png"
      contain
      transition="scale-transition"
      width="50"
      height="50"
      />
  </div>
  <v-dialog v-model="showAboutDialog" max-width="1200">
    <about-page @close="showAboutDialog = false" />
  </v-dialog>
  <v-dialog v-model="settingsDialog" @keydown.esc="settingsDialog = false" max-width="800">
    <settings-dialog @close="settingsDialog = false" />
  </v-dialog>
  <confirm-dialog ref="confirm" :text-cols="5" :action-cols="6">
    <template v-slot:actions>
      <v-btn
        color="white"
        @click.native="openSelectStudyDialog"
        outlined
        class="mr-2"
        elevation="2"
        >
        {{ $t('_global.select_study') }}
      </v-btn>
      <v-btn
        color="white"
        @click.native="redirectToStudyTable"
        outlined
        elevation="2"
        >
        {{ $t('_global.add_study') }}
      </v-btn>
    </template>
  </confirm-dialog>
  <v-dialog
    v-model="showSelectForm"
    persistent
    max-width="600px"
    >
    <study-quick-select-form @close="showSelectForm = false" @selected="reloadPage" />
  </v-dialog>
</v-app-bar>
</template>

<script>
import { mapGetters } from 'vuex'
import AboutPage from '@/components/layout/AboutPage'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import SettingsDialog from './SettingsDialog.vue'
import StudyQuickSelectForm from '@/components/studies/StudyQuickSelectForm'
import { accessGuard } from '@/mixins/accessRoleVerifier'

export default {
  mixins: [accessGuard],
  components: {
    AboutPage,
    ConfirmDialog,
    SettingsDialog,
    StudyQuickSelectForm
  },
  props: {
    hideAppBarNavIcon: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      selectedStudyVersion: 'studiesGeneral/selectedStudyVersion',
      helpUrl: 'app/helpUrl',
      section: 'app/section',
      userInfo: 'auth/userInfo'
    }),
    drawer: {
      get () { return this.$store.state.app.drawer },
      set (value) { return this.$store.commit('app/SET_DRAWER', value) }
    },
    app: {
      set (value) {
        this.$store.commit('app/SET_SECTION', value)
      },
      get () {
        return this.section
      }
    },
    documentationPortalUrl () {
      return this.$config.DOC_BASE_URL
    },
    username () {
      return (this.userInfo) ? this.userInfo.name : 'Anonymous'
    },
    availableApps () {
      return this.apps.filter(app => !app.needsAuthentication || this.isAuthenticated)
    },
    isAuthenticated () {
      return !this.$config.OAUTH_ENABLED || !!this.userInfo
    },
    currentStudyStatus () {
      if (!this.selectedStudy) {
        return null
      }
      return this.selectedStudy.current_metadata.version_metadata.study_status
    }
  },
  data () {
    return {
      apps: [
        {
          icon: 'mdi-stethoscope',
          name: 'Studies',
          needsAuthentication: true
        },
        {
          icon: 'mdi-bookshelf',
          name: 'Library',
          needsAuthentication: true
        }
      ],
      showAboutDialog: false,
      settingsDialog: false,
      showSelectForm: false
    }
  },
  methods: {
    navigateToRoot () {
      this.$emit('backToRoot')
    },
    openAboutBox () {
      this.showAboutDialog = true
    },
    openSettingsBox () {
      this.settingsDialog = true
    },
    openSelectStudyDialog () {
      this.showSelectForm = true
    },
    redirectToStudyTable () {
      this.$refs.confirm.cancel()
      this.$router.push({ name: 'SelectOrAddStudy' })
    },
    reloadPage () {
      const regex = /\/studies\/Study_[\d]+/
      const newUrl = document.location.href.replace(regex, '/studies/' + this.selectedStudy.uid)
      document.location.href = newUrl
    }
  }
}
</script>

<style scoped lang="scss">
.action {
  cursor: pointer;
}
.v-toolbar {
  &__items {
    align-items: center;
    .v-btn {
      height: 60% !important;
      &--active {
        &::before {
          opacity: 0
        }
        background-color: var(--v-secondary-base);
        border-radius: $border-radius-root * 2 !important;
      }
      &:hover {
        border-radius: $border-radius-root * 2 !important;
      }
    }
  }
}
</style>
