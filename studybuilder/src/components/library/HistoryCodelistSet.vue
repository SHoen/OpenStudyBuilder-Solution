<template>
<div>
  <div class="mb-4">
    {{ title }}
    <v-chip :color="color" class="white--text" small>{{ codelists.length }}</v-chip>
  </div>

  <div class="d-flex align-end flex-wrap">
    <template
      v-for="(codelists, date, dateIndex) in codelistsByDate"
      >
      <v-divider :key="dateIndex" v-if="dateIndex !== 0" class="mx-4" vertical></v-divider>
      <div
        v-for="(codelist, index) in codelists"
        :key="codelist.uid"
        class="mt-4"
        >
        <p v-if="index === 0" class="mb-4">{{ date }}</p>
        <v-badge
          :color="color"
          :content="getCodelistBadge(codelist)"
          class="mr-4 mb-2"
          overlap
          bordered
          >
          <v-chip :color="color" class="white--text" @click="openCodelistHistory(codelist)">
            {{ getCodelistName(codelist) }}
          </v-chip>
        </v-badge>
      </div>
    </template>
  </div>
</div>
</template>

<script>
export default {
  props: {
    title: String,
    color: String,
    codelists: Array,
    chipsLabel: String,
    fromDate: String,
    toDate: String
  },
  computed: {
    codelistsByDate () {
      const result = {}
      this.codelists.forEach(codelist => {
        const date = codelist.change_date.split('T')[0]
        if (result[date] === undefined) {
          result[date] = []
        }
        result[date].push(codelist)
      })
      return result
    }
  },
  methods: {
    getCodelistBadge (codelist) {
      return (codelist.is_change_of_codelist === undefined || codelist.is_change_of_codelist) ? 'C' : 'T'
    },
    getCodelistName (codelist) {
      if (this.chipsLabel === 'uid') {
        return codelist.uid
      }
      if (codelist.value_node[this.chipsLabel] !== undefined) {
        return codelist.value_node[this.chipsLabel]
      }
      if (codelist.value_node.inCommon && codelist.value_node.inCommon[this.chipsLabel] !== undefined) {
        return codelist.value_node.inCommon[this.chipsLabel]
      }
      if (codelist.value_node.different && codelist.value_node.different[this.chipsLabel] !== undefined) {
        return codelist.value_node.different[this.chipsLabel].right
      }
      return ''
    },
    openCodelistHistory (codelist) {
      this.$router.push({
        name: 'CtPackageCodelistHistory',
        params: {
          catalogueName: this.$route.params.catalogueName,
          codelistId: codelist.uid
        },
        query: {
          fromDate: this.fromDate,
          toDate: this.toDate
        }
      })
    }
  }
}
</script>

<style scoped lang="scss">
.codelist-set {
  border-left: 1px solid var(--v-greyBackground-base);
}
</style>
