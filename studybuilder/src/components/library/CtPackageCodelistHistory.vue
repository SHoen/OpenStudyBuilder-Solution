<template>
<div>
  <p><span class="v-label">{{ $t('CtPackageCodelistHistory.codelist_label') }}</span> {{ codelistAttributes.name }} [{{ codelistAttributes.codelistUid }}]</p>
  <div class="v-data-table">
    <div class="v-data-table__wrapper">
      <table class="mt-4 white">
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
            <td>{{ codelistAttributes.submissionValue }}</td>
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
      termLabels: {}
    }
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
        return 'mdi-pencil'
      }
      return 'mdi-trash'
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
          this.$set(this.termLabels, item.uid, resp.data.codeSubmissionValue)
        })
      }
      this.addChangeToList(item, this.terms[item.uid], type)
    }
  },
  created () {
    controlledTerminology.getCodelistAttributes(this.codelistUid).then(resp => {
      this.codelistAttributes = resp.data
    })
    controlledTerminology.getPackagesCodelistChanges(this.codelistUid, this.catalogueName, this.fromDate, this.toDate).then(resp => {
      this.loading = false
      resp.data.newCodelists.forEach(item => {
        this.addCodelistChange(item, 'added')
      })
      resp.data.updatedCodelists.forEach(item => {
        if (item.is_change_of_codelist) {
          this.addCodelistChange(item, 'updated')
        }
      })
      resp.data.deletedCodelists.forEach(item => {
        this.addCodelistChange(item, 'deleted')
      })
      resp.data.newTerms.forEach(item => {
        this.addTermChange(item, 'added')
      })
      resp.data.updatedTerms.forEach(item => {
        this.addTermChange(item, 'updated')
      })
      resp.data.deletedTerms.forEach(item => {
        this.addTermChange(item, 'deleted')
      })
      this.dates = this.dates.sort((a, b) => new Date(a) - new Date(b))
    })
  }
}
</script>
