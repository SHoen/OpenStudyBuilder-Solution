<template>
<div class="px-4">
  <div class="page-title">{{ $t('CtPackagesHistoryView.title') }}</div>
  <v-tabs v-model="tab" background-color="dfltBackground">
    <v-tab v-for="catalogue in catalogues"
           :key="catalogue.name"
           :href="`#${catalogue.name}`"
           :data-cy="catalogue.name"
           >
      {{ catalogue.name }}
    </v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item
      v-for="catalogue in catalogues"
      :key="catalogue.name"
      :id="catalogue.name"
      >
      <ct-package-history :catalogue="catalogue" />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import { mapActions } from 'vuex'
import controlledTerminology from '@/api/controlledTerminology'
import CtPackageHistory from '@/components/library/CtPackageHistory'

export default {
  components: {
    CtPackageHistory
  },
  data () {
    return {
      catalogues: [],
      tab: this.$route.params.catalogueName
    }
  },
  methods: {
    ...mapActions({
      addBreadcrumbsLevel: 'app/addBreadcrumbsLevel'
    })
  },
  mounted () {
    this.addBreadcrumbsLevel({
      text: this.$route.params.catalogueName,
      to: { name: 'CtPackages', params: this.$route.params },
      index: 3
    })
    this.addBreadcrumbsLevel({
      text: this.$t('_global.history'),
      to: { name: 'CtPackagesHistory', params: this.$route.params }
    })

    controlledTerminology.getCatalogues().then(resp => {
      this.catalogues = resp.data
    })
  },
  watch: {
    tab (newValue) {
      this.$router.push({
        name: 'CtPackagesHistory',
        params: { catalogueName: newValue }
      })
    }
  }
}
</script>
