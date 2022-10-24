<template>
<v-navigation-drawer
  app
  v-model="drawer"
  :mini-variant="mini"
  :expand-on-hover="mini"
  color="primary"
  width="290"
  :key="drawerRefreshKey"
  @transitionend="transitionEnd"
  dark
  clipped
  >
  <template v-slot:prepend="">
    <v-btn class="mt-1" style="margin-left: 10px" icon data-cy="toggle-sidebar" @click="toggleMenu">
      <v-icon v-if="mini">mdi-chevron-double-right</v-icon>
      <v-icon v-else>mdi-chevron-double-left</v-icon>
    </v-btn>
  </template>
  <v-list dense dark expand color="primary">
    <v-list-item-group v-model="selectedItem">
      <template v-for="(item, pos) in selectedItems">
        <v-list-item
          v-if="!item.children"
          active-class="submenu-item--active"
          :data-cy="item.title"
          :to="item.url"
          link
          exact
          dark
          :key="pos"
          @click="onMenuItemClick(item)"
          :disabled="item.disabled && item.disabled()"
          >
          <v-list-item-icon v-if="item.icon">
            <v-icon>{{ item.icon }}</v-icon>
          </v-list-item-icon>

          <v-list-item-content>
            <v-list-item-title>{{ item.title }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-group v-else
                      color="white"
                      :data-cy="item.title"
                      :key="pos"
                      :prepend-icon="item.icon"
                      :value="secondBreadcrumbsLevel && secondBreadcrumbsLevel.text === item.title"
                      no-action>
          <template v-slot:activator>
            <v-list-item-title>{{ item.title }}</v-list-item-title>
          </template>

          <v-list-item v-for="subitem in item.children"
                       class="submenu-item"
                       color="white"
                       :data-cy="subitem.title"
                       :key="subitem.title"
                       @click="onMenuItemClick(item, subitem)"
                       :disabled="subitem.disabled && subitem.disabled()"
                       :to="subitem.url"
                       link
                       :exact="(subitem.exact !== undefined) ? subitem.exact : false"
                       >
            <v-list-item-icon v-if="subitem.icon">
              <v-icon>{{ subitem.icon }}</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>{{ subitem.title }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list-group>
      </template>
    </v-list-item-group>
  </v-list>
  <redirect-handler :target="target"/>
</v-navigation-drawer>
</template>

<script>
import { mapGetters } from 'vuex'
import RedirectHandler from '@/components/tools/RedirectHandler'

export default {
  components: {
    RedirectHandler
  },
  computed: {
    ...mapGetters({
      section: 'app/section',
      getBreadcrumbsLevel: 'app/getBreadcrumbsLevel',
      selectedStudy: 'studiesGeneral/selectedStudy',
      menuItems: 'app/menuItems',
      studyUid: 'app/studyUid'
    }),
    drawer: {
      get () { return this.$store.state.app.drawer },
      set (value) { return this.$store.commit('app/SET_DRAWER', value) }
    },
    selectedItems () {
      if (this.section && Object.prototype.hasOwnProperty.call(this.menuItems, this.section)) {
        return this.menuItems[this.section].items
      }
      return []
    },
    secondBreadcrumbsLevel () {
      return this.getBreadcrumbsLevel(1)
    }
  },
  data () {
    return {
      drawerRefreshKey: 1,
      nextUrl: null,
      refreshNeeded: false,
      selectedItem: 0,
      mini: false,
      showSelectForm: false,
      studyId: '',
      target: {}
    }
  },
  methods: {
    async onMenuItemClick (item, subitem) {
      this.target = { subitem: subitem, item: item }
    },
    toggleMenu () {
      this.mini = !this.mini
      this.refreshNeeded = true
      localStorage.setItem('narrowMenu', JSON.stringify(this.mini))
    },
    transitionEnd () {
      if (this.refreshNeeded) {
        this.drawerRefreshKey += 1
        this.refreshNeeded = false
      }
    }
  },
  mounted () {
    this.studyId = this.studyUid
    if (JSON.parse(localStorage.getItem('narrowMenu')) === true) {
      this.mini = true
    }
    this.selected = this.selectedStudy
  },
  watch: {
    selected: function (val) {
      if (val) {
        this.studyId = val.uid
      } else {
        this.studyId = null
      }
    }
  }
}
</script>

<style scoped lang="scss">
.top-logo {
  height: 64px;
  cursor: pointer;
}
.submenu-item {
  background-color: var(--v-nnLightBlue1-base);
}
.v-list-item {
  &--active {
    background-color: var(--v-nnLightBlue2-base) !important;
    &::before {
      opacity: 0 !important;
    }
    .v-list-item__title {
      font-weight: 700 !important;
    }
  }
}
</style>
