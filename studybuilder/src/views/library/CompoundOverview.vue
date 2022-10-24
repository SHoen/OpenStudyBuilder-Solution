<template>
<div class="px-4">
  <div class="d-flex page-title">
    {{ compound.name }}
  </div>
  <compound-overview :compound="compound" />
</div>
</template>

<script>
import CompoundOverview from '@/components/library/CompoundOverview'
import compounds from '@/api/concepts/compounds'
import { mapActions } from 'vuex'

export default {
  components: {
    CompoundOverview
  },
  data () {
    return {
      compound: {}
    }
  },
  methods: {
    ...mapActions({
      addBreadcrumbsLevel: 'app/addBreadcrumbsLevel'
    })
  },
  created () {
    compounds.getObject(this.$route.params.id).then(resp => {
      this.compound = resp.data
      this.addBreadcrumbsLevel({
        text: this.compound.name,
        to: { name: 'CompoundOverview', params: this.$route.params },
        index: 3
      })
    })
  }
}
</script>
