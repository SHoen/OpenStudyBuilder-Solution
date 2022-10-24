<template>
<div>
  <v-tabs v-model="tab" background-color="dfltBackground">
    <v-tab v-for="(packages, catalogue) in packages"
           :key="catalogue"
           :href="`#${catalogue}`"
           :data-cy="catalogue"
           >
      {{ catalogue }}
    </v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item
      v-for="(cataloguePackages, catalogue) in packages"
      :key="catalogue"
      :id="catalogue"
      >
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="1" class="flex-grow-1 flex-shrink-0" style="min-width: 100px; max-width: 200px;">
          <v-timeline data-cy="timeline" dense class="mr-4">
            <v-timeline-item
              v-for="(pkg, index) in cataloguePackages"
              :key="index"
              :color="pkg.name === cataloguePackages.selectedPackage ? 'primary' : 'grey'"
              small
              >
              <v-btn
                text
                :color="cataloguePackages.selectedPackage === pkg.name ? 'primary' : 'default'"
                @click.stop="selectPackage(catalogue, pkg.name, true)"
                data-cy="timeline-date"
                >
                {{ displayDate(pkg.date) }}
              </v-btn>
            </v-timeline-item>
          </v-timeline>
        </v-col>
        <v-col cols="10" style="min-width: 100px; max-width: 100%;" class="flex-grow-1 flex-shrink-0 pb-4">
          <slot :catalogueName="catalogue" v-bind:selectedPackage="packages[catalogue].selectedPackage" />
        </v-col>
      </v-row>
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import { DateTime } from 'luxon'
import controlledTerminology from '@/api/controlledTerminology'

export default {
  props: {
    catalogueName: {
      type: String,
      required: false
    },
    packageName: {
      type: String,
      required: false
    }
  },
  data () {
    return {
      packages: [],
      tab: null
    }
  },
  methods: {
    displayDate (date) {
      return DateTime.fromJSDate(date).toISODate()
    },
    selectPackage (catalogue, pkg, sendEvent) {
      if (sendEvent) {
        this.$emit('packageChanged', catalogue, pkg)
      }
      this.$set(this.packages[catalogue], 'selectedPackage', pkg)
    },
    sortPackages (packages) {
      const result = {}
      packages.forEach(pkg => {
        if (result[pkg.catalogueName] === undefined) {
          result[pkg.catalogueName] = []
        }
        const date = DateTime.fromISO(pkg.effectiveDate).toJSDate()
        result[pkg.catalogueName].push({ date, name: pkg.name, selectedPackage: null })
      })
      for (const catalogue in result) {
        result[catalogue].sort((a, b) => {
          return b.date - a.date
        })
      }
      return result
    }
  },
  mounted () {
    controlledTerminology.getPackages().then(resp => {
      this.packages = this.sortPackages(resp.data)
      if (this.catalogueName) {
        this.tab = this.catalogueName
        if (this.packageName) {
          this.selectPackage(this.catalogueName, this.packageName)
        } else {
          this.selectPackage(this.catalogueName, this.packages[this.catalogueName][0].name)
        }
      } else {
        this.tab = Object.keys(this.packages)[0]
        this.selectPackage(this.tab, this.packages[this.tab][0].name)
      }
    })
  },
  watch: {
    tab (newValue, oldValue) {
      if (oldValue) {
        this.$emit('catalogueChanged', newValue)
      }
      if (newValue !== this.catalogueName) {
        this.$store.commit('ctCatalogues/SET_CURRENT_CATALOGUE_PAGE', 1)
      }
    },
    catalogueName (newValue) {
      if (this.packages[newValue]) {
        if (this.packageName) {
          this.selectPackage(newValue, this.packageName, true)
        } else {
          this.selectPackage(newValue, this.packages[newValue][0].name, true)
        }
      }
    }
  }
}
</script>

<style scoped lang="scss">
.v-tabs-items {
  background-color: var(--v-dfltBackground-base) !important;
}
</style>
