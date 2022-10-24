<template>
<div class="px-4">
  <div data-cy="page-title" class="page-title d-flex align-center">
    {{ $t('CtPackagesView.title') }}
    <help-button :help-text="$t('_help.CtPackagesTable.general')" />
  </div>
  <ct-packages-table
    :catalogueName="$route.params.catalogueName"
    :packageName="$route.params.packageName"
    />
</div>
</template>

<script>
import { mapActions } from 'vuex'
import CtPackagesTable from '@/components/library/CtPackagesTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    CtPackagesTable,
    HelpButton
  },
  methods: {
    ...mapActions({
      addBreadcrumbsLevel: 'app/addBreadcrumbsLevel'
    }),
    updateCatalogueInBreadcrumbs (catalogueName, replace) {
      this.addBreadcrumbsLevel({
        text: catalogueName,
        to: { name: 'CtPackages', params: { catalogueName } },
        index: 3,
        replace
      })
    },
    updatePackageInBreadcrumbs (packageName, catalogueName, replace) {
      this.addBreadcrumbsLevel({
        text: packageName,
        to: { name: 'CtPackages', params: { catalogueName, packageName } },
        index: 4,
        replace
      })
    }
  },
  mounted () {
    if (this.$route.params.catalogueName) {
      this.updateCatalogueInBreadcrumbs(this.$route.params.catalogueName)
    }
    if (this.$route.params.packageName) {
      this.updatePackageInBreadcrumbs(this.$route.params.packageName, this.$route.params.catalogueName)
    }
  },
  watch: {
    '$route.params.catalogueName' (value) {
      this.updateCatalogueInBreadcrumbs(value, true)
    },
    '$route.params.packageName' (value) {
      if (value) {
        this.updatePackageInBreadcrumbs(value, this.$route.params.catalogueName, true)
      } else {
        this.$store.commit('app/TRUNCATE_BREADCRUMBS_FROM_LEVEL', 4)
      }
    }
  }
}
</script>
