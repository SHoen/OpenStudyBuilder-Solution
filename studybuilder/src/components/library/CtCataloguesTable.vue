<template>
<div>
  <v-tabs v-model="tab">
    <v-tab v-for="catalogue in allCatalogues"
           :data-cy="catalogue.name"
           :key="catalogue.name"
           :href="`#${catalogue.name}`"
           >
      {{ catalogue.name }}
    </v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item
      v-for="catalogue in allCatalogues"
      :key="catalogue.name"
      :id="catalogue.name"
      >
      <codelist-table
        :catalogue="catalogue.name"
        @openCodelistTerms="openCodelistTerms"
        column-data-resource="ct/codelists"
        />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import CodelistTable from './CodelistTable'

export default {
  components: {
    CodelistTable
  },
  props: ['catalogueName'],
  computed: {
    ...mapGetters({
      catalogues: 'ctCatalogues/catalogues'
    }),
    allCatalogues () {
      const array = [{ name: 'All' }]
      return array.concat(this.catalogues)
    }
  },
  data () {
    return {
      tab: null,
      originalCatalogue: null
    }
  },
  methods: {
    openCodelistTerms ({ codelist, catalogueName }) {
      this.$router.push({
        name: 'CodelistTerms',
        params: { codelistId: codelist.codelistUid }
      })
    }
  },
  mounted () {
    this.originalCatalogue = this.catalogueName
    this.$store.dispatch('ctCatalogues/fetchCatalogues')
  },
  watch: {
    tab (newValue, oldValue) {
      if (newValue !== this.catalogueName) {
        this.$store.commit('ctCatalogues/SET_CURRENT_CATALOGUE_PAGE', 1)
      }
      this.$emit('catalogueChanged', newValue)
    },
    catalogues (newValue) {
      this.tab = this.originalCatalogue
    }
  }
}
</script>
