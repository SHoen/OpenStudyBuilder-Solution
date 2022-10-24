<template>
<v-card elevation="0" outlined>
  <v-card-title>
    <v-row no-gutters>
      <v-col cols="10">
        <div class="d-flex">
          <div v-for="(date, index) in dates" :key="index" class="mx-2">
            <div class="text-caption">{{ shortDate(date) }}</div>
            <div class="text-center">
              <v-btn fab :color="getDateColor(date)" x-small @click="selectDate(date)"></v-btn>
            </div>
          </div>
        </div>
      </v-col>
      <v-col cols="2" class="d-flex">
        <label class="v-label mr-4">{{ $t('CtPackageHistory.show') }}</label>
        <v-radio-group v-model="display" dense>
          <v-radio
            :label="$t('CtPackageHistory.submission_value_choice')"
            value="submission_value"
            />
          <v-radio
            :label="$t('CtPackageHistory.codelist_code_choice')"
            value="uid"
            />
          <v-radio
            :label="$t('CtPackageHistory.sponsor_name_choice')"
            value="name"
            />
        </v-radio-group>
      </v-col>
    </v-row>
  </v-card-title>
  <div class="d-flex align-center greyBackground py-4 px-16" v-if="fromDate && toDate">
    <v-btn fab color="secondary" x-small class="mr-2"></v-btn>
    <span>From {{ shortDate(fromDate) }}</span>
    <v-divider class="mx-10" />
    <v-btn fab color="secondary" x-small class="mr-2"></v-btn>
    <span>To {{ shortDate(toDate) }}</span>
  </div>
  <div v-if="fromDate && toDate" class="pa-4">
    <v-progress-linear v-if="loading" indeterminate class="mx-4" />
    <template v-else>
      <history-codelist-set
        :title="$tc('CtPackageHistory.new_codelist', changes.newCodelists.length)"
        color="primary"
        :codelists="changes.newCodelists"
        :chips-label="display"
        :from-date="fromDate"
        :to-date="toDate"
        />
      <v-divider class="my-4" color="greyBackground" />
      <history-codelist-set
        :title="$tc('CtPackageHistory.updated_codelist', changes.updatedCodelists.length)"
        color="green"
        :codelists="changes.updatedCodelists"
        :chips-label="display"
        :from-date="fromDate"
        :to-date="toDate"
        />
      <v-divider class="my-4" color="greyBackground" />
      <history-codelist-set
        :title="$tc('CtPackageHistory.deleted_codelist', changes.deletedCodelists.length)"
        color="red"
        :codelists="changes.deletedCodelists"
        :chips-label="display"
        :from-date="fromDate"
        :to-date="toDate"
        />
    </template>
  </div>
</v-card>
</template>

<script>
import { DateTime } from 'luxon'
import controlledTerminology from '@/api/controlledTerminology'
import HistoryCodelistSet from './HistoryCodelistSet'

export default {
  props: ['catalogue'],
  components: {
    HistoryCodelistSet
  },
  data () {
    return {
      changes: {},
      dates: [],
      display: 'submission_value',
      fromDate: null,
      loading: false,
      toDate: null
    }
  },
  methods: {
    resetChanges () {
      this.changes = {
        newCodelists: {},
        deletedCodelists: {},
        updatedCodelists: {}
      }
    },
    getDateColor (date) {
      return (this.fromDate === date || this.toDate === date) ? 'secondary' : ''
    },
    async selectDate (date) {
      if (!this.fromDate) {
        this.fromDate = date
      } else if (!this.toDate) {
        const fromDate = DateTime.fromISO(this.fromDate).toJSDate()
        const toDate = DateTime.fromISO(date).toJSDate()
        if (fromDate < toDate) {
          this.toDate = date
        } else {
          this.toDate = this.fromDate
          this.fromDate = date
        }
        this.loading = true
        try {
          const resp = await controlledTerminology.getPackagesChanges(this.catalogue.name, this.fromDate, this.toDate)
          this.changes = resp.data
        } finally {
          this.loading = false
        }
      } else {
        this.resetChanges()
        this.fromDate = date
        this.toDate = null
      }
    },
    shortDate (value) {
      return value.split('T')[0]
    }
  },
  mounted () {
    this.resetChanges()
    controlledTerminology.getPackagesDates(this.catalogue.name).then(resp => {
      this.dates = resp.data.effectiveDates
    })
  }
}
</script>
