<template>
<div class="px-4">
  <div class="page-title">
    {{ codelistAttributes.name }} ({{ $route.params.codelistId }}) - {{ codelistAttributes.submissionValue }} / {{ $t('CodelistTermsView.terms_listing') }}
  </div>
  <codelist-term-table
    :catalogueName="$route.params.catalogueName"
    :codelistUid="$route.params.codelistId"
    />
</div>
</template>

<script>
import { mapActions } from 'vuex'
import controlledTerminology from '@/api/controlledTerminology'
import CodelistTermTable from '@/components/library/CodelistTermTable'

export default {
  components: {
    CodelistTermTable
  },
  data () {
    return {
      codelistAttributes: {}
    }
  },
  methods: {
    ...mapActions({
      addBreadcrumbsLevel: 'app/addBreadcrumbsLevel'
    })
  },
  mounted () {
    this.addBreadcrumbsLevel({
      text: this.$route.params.codelistId,
      to: { name: 'CodeListDetail', params: this.$route.params },
      index: 4
    })
    this.addBreadcrumbsLevel({
      text: this.$t('CodelistTermsView.terms'),
      to: { name: 'CodelistTerms', params: this.$route.params }
    })
    controlledTerminology.getCodelistAttributes(this.$route.params.codelistId).then(resp => {
      this.codelistAttributes = resp.data
    })
  }
}
</script>
