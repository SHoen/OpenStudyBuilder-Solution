<template>
  <div class="fullscreen-bg">
    <h1>{{ $t('_global.library') }}</h1>
    <p>{{ $t('Library.description_top_before') }} <strong>{{ $t('_global.library') }}</strong>
      {{ $t('Library.description_top_after') }}</p>
    <p>{{ $t('Library.description_bottom') }}</p>
    <v-row class="mt-6 justify-center box-container">
      <v-col cols="8" xs="4" sm="4" md="3" lg="3" class="item" v-for="item in startFrom(libraryMenu.items, 1)" :key="item.title">
        <div class="white--text item-content" :id="item.id">
          <v-menu bottom offset-y>
            <template v-slot:activator="{ on, attrs }">
              <div class="d-flex align-center pa-1">
                <v-icon large color="white">{{ item.icon }}</v-icon>
                <span class="mx-2 text-h6">{{ item.title }}</span>
                <v-spacer />
                <v-btn icon v-if="item.children" color="white" v-bind="attrs" v-on="on">
                  <v-icon>mdi-menu</v-icon>
                </v-btn>
              </div>
            </template>
            <v-list>
              <v-list-item
                v-for="(item, index) in item.children"
                :key="index"
                :to="item.url"
                >
                <v-list-item-title>{{ item.title }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
        <expandable-header-content :item="item"/>
      </v-col>
    </v-row>
  </div>
</template>

<script>

import { mapGetters } from 'vuex'
import ExpandableHeaderContent from '@/components/tools/ExpandableHeaderContent'

export default {
  computed: {
    ...mapGetters({
      libraryMenu: 'app/libraryMenu'
    })
  },
  components: {
    ExpandableHeaderContent
  },
  data () {
    return {
    }
  },
  methods: {
    startFrom (arr, idx) {
      return arr.slice(idx)
    }
  }
}
</script>

<style scoped>
  .fullscreen-bg {
    background-image: url('../../assets/library-background.jpg');
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
