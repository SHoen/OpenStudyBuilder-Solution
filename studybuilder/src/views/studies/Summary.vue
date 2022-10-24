<template>
<div class="fullscreen-bg">
  <h1>{{ $t('_global.studies') }}</h1>
  <p>{{ $t('Studies.description_top_before') }} <strong>{{ $t('_global.studies') }}</strong>
    {{ $t('Studies.description_top_after') }}</p>
  <p>{{ $t('Studies.description_bottom') }}</p>
  <v-row data-cy="tiles-box" class="mt-6 justify-center box-container">
    <v-col cols="8" xs="4" sm="4" md="3" lg="3" class="item" v-for="item in startFrom(studiesMenu.items, 1)" :key="item.title" :data-cy="item.title">
      <div class="white--text item-content" :id="item.id">
        <v-menu bottom offset-y>
          <template v-slot:activator="{ on, attrs }">
            <div class="d-flex align-center pa-1">
              <v-icon color="white">{{ item.icon }}</v-icon>
              <span class="mx-2 text-h6">{{ item.title }}</span>
              <v-spacer />
              <v-btn data-cy="dropdown-button" icon v-if="item.children" color="white" v-bind="attrs" v-on="on">
                <v-icon>mdi-menu</v-icon>
              </v-btn>
            </div>
          </template>
          <v-list>
            <v-list-item
              v-for="(subitem, index) in item.children"
              :key="index"
              @click="redirect(subitem, item)"
              >
              <v-list-item-title>{{ subitem.title }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
      <expandable-header-content :item="item"/>
    </v-col>
  </v-row>
  <redirect-handler :target="target"/>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import ExpandableHeaderContent from '@/components/tools/ExpandableHeaderContent'
import RedirectHandler from '@/components/tools/RedirectHandler'

export default {
  computed: {
    ...mapGetters({
      studiesMenu: 'app/studiesMenu',
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  components: {
    ExpandableHeaderContent,
    RedirectHandler
  },
  mounted () {
    this.items = this.studies
  },
  data () {
    return {
      items: [],
      expanded: false,
      showSelectForm: false,
      nextUrl: null,
      target: {}
    }
  },
  methods: {
    startFrom (arr, idx) {
      return arr.slice(idx)
    },
    async redirect (subitem, item) {
      this.target = { subitem: subitem, item: item }
    }
  }
}
</script>

<style scoped>
  .fullscreen-bg {
    background-image: url('../../assets/studies_background.jpg');
  }
  h1 {
    margin-bottom: 1rem;
    font-size: 60px;
  }
  p {
    font-size: 20px;
  }
  .item {
    padding: 0px;
    margin: 20px;
  }
  .item-content {
    background: #6675A3;
  }
  .item-description {
    background: #fff;
    padding: 5px;
  }
</style>
