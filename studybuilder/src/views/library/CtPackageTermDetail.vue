<template>
<package-timeline
  :catalogueName="$route.params.catalogueName"
  :packageName="$route.params.packageName"
  @catalogueChanged="updateCatalogue"
  @packageChanged="updateTerms"
  >
  <template v-slot:default="{ selectedPackage }">
    <div class="page-title">
      {{ $t('CodelistTermsView.codelist') }} {{ $route.params.codelistId }} - {{ codelistAttributes.submissionValue }} / {{ $t('CodelistTermDetail.term_detail') }} ({{ $t('CodelistTermDetail.concept_id') }}: {{ $route.params.termId }})
    </div>
    <codelist-term-detail
      :codelistUid="$route.params.codelistId"
      :termUid="$route.params.termId"
      :packageName="selectedPackage"
      />
  </template>
</package-timeline>
</template>

<script>
import controlledTerminology from '@/api/controlledTerminology'
import CodelistTermDetail from '@/components/library/CodelistTermDetail'
import PackageTimeline from '@/components/library/PackageTimeline'

export default {
  components: {
    CodelistTermDetail,
    PackageTimeline
  },
  data () {
    return {
      codelistAttributes: {}
    }
  },
  methods: {
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
    this.$store.dispatch('app/addBreadcrumbsLevel', {
      text: this.$route.params.termId,
      index: 7
    })
    controlledTerminology.getCodelistAttributes(this.$route.params.codelistId).then(resp => {
      this.codelistAttributes = resp.data
    })
  }
}
</script>
