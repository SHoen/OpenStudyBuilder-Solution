<template>
<div class="px-4">
  <div class="page-title">
    {{ $t('CodelistTermsView.codelist') }} {{ $route.params.codelistId }} - {{ codelistAttributes.submissionValue }} / {{ $t('CodelistTermDetail.term_detail') }} ({{ $t('CodelistTermDetail.concept_id') }}: {{ $route.params.termId }})
  </div>
  <codelist-term-detail
    :codelistUid="$route.params.codelistId"
    :termUid="$route.params.termId"
    />
</div>
</template>

<script>
import controlledTerminology from '@/api/controlledTerminology'
import CodelistTermDetail from '@/components/library/CodelistTermDetail'

export default {
  components: {
    CodelistTermDetail
  },
  data () {
    return {
      codelistAttributes: {}
    }
  },
  mounted () {
    this.$store.dispatch('app/addBreadcrumbsLevel', {
      text: this.$route.params.termId,
      index: 6
    })
    controlledTerminology.getCodelistAttributes(this.$route.params.codelistId).then(resp => {
      this.codelistAttributes = resp.data
    })
  }
}
</script>
