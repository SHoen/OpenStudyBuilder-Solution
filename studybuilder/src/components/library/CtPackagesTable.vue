<template>
<package-timeline
  :catalogueName="catalogueName"
  :packageName="packageName"
  @catalogueChanged="updateUrl"
  @packageChanged="updateUrl"
  >
  <template v-slot:default="{ catalogueName, selectedPackage }">
    <codelist-table
      :package="selectedPackage"
      table-height="50vh"
      read-only
      @openCodelistTerms="openCodelistTerms"
      column-data-resource="ct/codelists"
      >
      <template v-slot:extraActions>
        <v-btn
          class="mx-2"
          fab
          small
          @click="goToPackagesHistory(catalogueName)"
          >
          <v-icon>mdi-calendar-clock</v-icon>
        </v-btn>
      </template>
    </codelist-table>
  </template>
</package-timeline>
</template>

<script>
import CodelistTable from './CodelistTable'
import PackageTimeline from './PackageTimeline'

export default {
  props: ['catalogueName', 'packageName'],
  components: {
    CodelistTable,
    PackageTimeline
  },
  methods: {
    openCodelistTerms ({ codelist, packageName }) {
      this.$router.push({
        name: 'CtPackageTerms',
        params: { codelistId: codelist.codelistUid, packageName: packageName }
      })
    },
    updateUrl (catalogueName, packageName) {
      this.$router.push({
        name: 'CtPackages',
        params: { catalogueName: catalogueName, packageName: packageName }
      })
    },
    goToPackagesHistory (catalogueName) {
      this.$router.push({
        name: 'CtPackagesHistory',
        params: { catalogueName }
      })
    }
  }
}
</script>
