<template>
<div class="px-4">
  <div class="page-title">{{ $t('CtPackageCodelistHistoryView.title') }}</div>
  <ct-package-codelist-history
    :catalogue-name="$route.params.catalogueName"
    :codelist-uid="$route.params.codelistId"
    :from-date="$route.query.fromDate"
    :to-date="$route.query.toDate"
    />
</div>
</template>

<script>
import { mapActions } from 'vuex'
import CtPackageCodelistHistory from '@/components/library/CtPackageCodelistHistory'

export default {
  components: {
    CtPackageCodelistHistory
  },
  methods: {
    ...mapActions({
      addBreadcrumbsLevel: 'app/addBreadcrumbsLevel'
    })
  },
  mounted () {
    this.addBreadcrumbsLevel({
      text: this.$route.params.codelistId
    })
  }
}
</script>
