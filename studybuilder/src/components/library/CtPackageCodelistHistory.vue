<template>
<div v-resize="onResize">
  <p><span class="v-label">{{ $t('CtPackageCodelistHistory.codelist_label') }}</span> {{ codelistAttributes.name }} [{{ codelistAttributes.codelist_uid }}]</p>
  <div class="v-data-table">
    <div ref="tableContainer" class="v-data-table__wrapper sticky-header" :style="`height: ${tableHeight}px`">
      <table class="mt-4 white" :aria-label="$t('CtPackageCodelistHistory.codelist_label')">
        <thead>
          <tr class="greyBackground">
            <th>{{ $t('CtPackageCodelistHistory.first_col_label') }}</th>
            <th v-for="date in dates" :key="date">{{ date }}</th>
          </tr>
        </thead>
        <v-progress-linear
          v-if="loading"
          color="primary"
          indeterminate
          />
        <tbody>
          <tr>
            <td>{{ codelistAttributes.submission_value }}</td>
            <td v-for="date in dates" :key="date">
              <template v-if="codelistChanges[date]">
                <v-btn fab x-small :color="getButtonColor(codelistChanges[date])">
                  <v-icon color="white">{{ getButtonIcon(codelistChanges[date]) }}</v-icon>
                </v-btn>
              </template>
            </td>
          </tr>
          <tr v-for="(change, term) in terms" :key="term">
            <td class="pl-10">{{ termLabels[term] }}</td>
            <td v-for="date in dates" :key="date">
              <template v-if="change[date]">
                <v-btn fab x-small :color="getButtonColor(change[date])">
                  <v-icon color="white">{{ getButtonIcon(change[date]) }}</v-icon>
                </v-btn>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
</template>

<script>
import controlledTerminology from '@/api/controlledTerminology'

export default {
  props: {
    catalogueName: String,
    codelistUid: String,
    fromDate: String,
    toDate: String
  },
  data () {
    return {
      codelistAttributes: {},
      dates: [],
      codelistChanges: {},
      loading: true,
      terms: {},
      termLabels: {},
      tableHeight: 500
    }
  },
  mounted () {
    this.onResize()
  },
  methods: {
    getButtonColor (change) {
      if (change.added) {
        return 'primary'
      }
      if (change.updated) {
        return 'green'
      }
      return 'red'
    },
    getButtonIcon (change) {
      if (change.added) {
        return 'mdi-plus'
      }
      if (change.updated) {
        return 'mdi-pencil-outline'
      }
      return 'mdi-delete-outline'
    },
    addChangeToList (item, changeList, type) {
      const date = item.change_date.split('T')[0]
      if (this.dates.indexOf(date) === -1) {
        this.dates.push(date)
      }
      const attrs = {}
      attrs[type] = true
      this.$set(changeList, date, attrs)
    },
    addCodelistChange (item, type) {
      this.addChangeToList(item, this.codelistChanges, type)
    },
    addTermChange (item, type) {
      if (this.terms[item.uid] === undefined) {
        this.$set(this.terms, item.uid, {})
        controlledTerminology.getCodelistTermAttributes(item.uid).then(resp => {
          this.$set(this.termLabels, item.uid, resp.data.code_submission_value)
        })
      }
      this.addChangeToList(item, this.terms[item.uid], type)
    },
    onResize () {
      this.tableHeight = window.innerHeight - this.$refs.tableContainer.getBoundingClientRect().y - 40
    }
  },
  created () {
    controlledTerminology.getCodelistAttributes(this.codelistUid).then(resp => {
      this.codelistAttributes = resp.data
    })
    controlledTerminology.getPackagesCodelistChanges(this.codelistUid, this.catalogueName, this.fromDate, this.toDate).then(resp => {
      this.loading = false
      resp.data.new_codelists.forEach(item => {
        this.addCodelistChange(item, 'added')
      })
      resp.data.updated_codelists.forEach(item => {
        if (item.is_change_of_codelist) {
          this.addCodelistChange(item, 'updated')
        }
      })
      resp.data.deleted_codelists.forEach(item => {
        this.addCodelistChange(item, 'deleted')
      })
      resp.data.new_terms.forEach(item => {
        this.addTermChange(item, 'added')
      })
      resp.data.updated_terms.forEach(item => {
        this.addTermChange(item, 'updated')
      })
      resp.data.deleted_terms.forEach(item => {
        this.addTermChange(item, 'deleted')
      })
      this.dates = this.dates.sort((a, b) => new Date(a) - new Date(b))
    })
  }
}
</script>
<style scoped lang="scss">
table {
  border-collapse: collapse;
}
tbody tr {
  border-bottom: 1px solid var(--v-greyBackground-base);
}
th {
  background-color: var(--v-greyBackground-base);
}
.sticky-header {
  overflow-y: auto;

  thead th {
    position: sticky;
    top: 0;
    z-index: 3;
  }
}
</style>
