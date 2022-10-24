<template>
<package-timeline
  @catalogueChanged="updateCatalogue"
  @packageChanged="updateTerms"
  :catalogueName="$route.params.catalogueName"
  :packageName="$route.params.packageName"
  >
  <template v-slot:default="{ selectedPackage }">
    <div class="page-title">
      {{ $t('CodelistTermsView.codelist') }} {{ $route.params.codelistId }} - {{ codelistAttributes.submissionValue }} / {{ $t('CodelistTermsView.terms_listing') }}
    </div>
    <codelist-term-table
      :catalogueName="$route.params.catalogueName"
      :codelistUid="$route.params.codelistId"
      :packageName="selectedPackage"
      />
  </template>
</package-timeline>
</template>

<script>
import { mapActions } from 'vuex'
import controlledTerminology from '@/api/controlledTerminology'
import CodelistTermTable from '@/components/library/CodelistTermTable'
import PackageTimeline from '@/components/library/PackageTimeline'

export default {
  components: {
    CodelistTermTable,
    PackageTimeline
  },
  data () {
    return {
      codelistAttributes: {}
    }
  },
  methods: {
    ...mapActions({
      addBreadcrumbsLevel: 'app/addBreadcrumbsLevel'
    }),
    updateCatalogue (catalogueName) {
      this.$router.push({
        name: 'CtPackages',
        params: { catalogueName }
      })
    },
    updateTerms (catalogueName, packageName) {
      this.$router.push({
        name: 'CtPackageTerms',
        params: {
          codelistId: this.$route.params.codelistId,
          catalogueName,
          packageName
        }
      })
    }
  },
  mounted () {
    this.addBreadcrumbsLevel({
      text: this.$route.params.codelistId,
      to: { name: 'CtPackages', params: this.$route.params },
      index: 5
    })
    this.addBreadcrumbsLevel({
      text: this.$t('CodelistTermsView.terms'),
      to: { name: 'CtPackageTerms', params: this.$route.params }
    })
    controlledTerminology.getCodelistAttributes(this.$route.params.codelistId).then(resp => {
      this.codelistAttributes = resp.data
    })
  },
  watch: {
    '$route.params.packageName' (value) {
      if (value) {
        const to = { name: 'CtPackages', params: { catalogueName: this.$route.params.catalogueName, packageName: value } }
        this.addBreadcrumbsLevel({ text: value, to, index: 4, replace: true })
      } else {
        this.$store.commit('app/TRUNCATE_BREADCRUMBS_FROM_LEVEL', 4)
      }
    }
  }

}
</script>
