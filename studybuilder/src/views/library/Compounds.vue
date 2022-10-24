<template>
<div class="px-4">
  <div class="d-flex page-title">
    {{ $t("CompoundsView.title") }}
    <help-button
      :title="$t('_global.definition')"
      :help-text="$t('_help.CompoundsView.general')"
      />
  </div>
  <v-tabs v-model="tab">
    <v-tab href="#compounds">{{ $t("CompoundsView.tab1_title") }}</v-tab>
    <v-tab href="#aliases">{{ $t("CompoundsView.tab2_title") }}</v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item id="compounds">
      <compound-table :tabClickedAt="compoundsTabClickedAt" />
    </v-tab-item>
    <v-tab-item id="aliases">
      <compound-alias-table :tabClickedAt="compoundAliasesTabClickedAt" />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import CompoundAliasTable from '@/components/library/CompoundAliasTable'
import CompoundTable from '@/components/library/CompoundTable'
import HelpButton from '@/components/tools/HelpButton'
import { mapActions } from 'vuex'

export default {
  components: {
    CompoundAliasTable,
    CompoundTable,
    HelpButton
  },
  methods: {
    ...mapActions({
      addBreadcrumbsLevel: 'app/addBreadcrumbsLevel'
    })
  },
  data () {
    return {
      tab: 1,
      compoundAliasesTabClickedAt: 0,
      compoundsTabClickedAt: 0
    }
  },
  mounted () {
    this.tab = this.$route.params.tab
    this.addBreadcrumbsLevel({
      text: this.$route.name,
      to: { name: 'Compounds', params: this.$route.params },
      index: 2
    })
  },
  watch: {
    tab (newValue) {
      switch (newValue) {
        case 'compounds':
          this.compoundsTabClickedAt = Date.now()
          break
        case 'aliases':
          this.compoundAliasesTabClickedAt = Date.now()
          break
      }
      this.$router.push({
        name: 'Compounds',
        params: { tab: newValue }
      })
    }
  }
}
</script>
