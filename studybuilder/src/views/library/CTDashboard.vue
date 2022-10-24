<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('CTDashboardView.title') }}
    <help-button :help-text="$t('_help.CTDashboard.general')" />
  </div>
  <div class="text-center mt-10" v-if="stats.catalogues === undefined">
    <v-progress-circular
      indeterminate
      color="primary"
      size="128"
      ></v-progress-circular>
  </div>
  <template v-else>
    <v-row >
      <v-col sm="12" lg="4">
        <v-card class="fixed-height" flat>
          <v-card-text>
            <div>
              {{ $t('CTDashboardView.catalogue_count') }} <span class="font-weight-bold">{{ stats.catalogues }}</span><br>
              {{ $t('CTDashboardView.package_count') }} <span class="font-weight-bold">{{ stats.packages }}</span>
            </div>
            <div class="mt-4">
              {{ $t('CTDashboardView.cdisc_codelist_count') }} <span class="font-weight-bold">{{ getCodelistCount('CDISC') }}</span><br>
              {{ $t('CTDashboardView.sponsor_codelist_count') }} <span class="font-weight-bold">{{ getCodelistCount('Sponsor') }}</span>
            </div>
            <div class="mt-4">
              {{ $t('CTDashboardView.cdisc_term_count') }} <span class="font-weight-bold">{{ getTermCount('CDISC') }}</span><br>
              {{ $t('CTDashboardView.sponsor_term_count') }} <span class="font-weight-bold">{{ getTermCount('Sponsor') }}</span>
            </div>
            <div class="mt-4">
              {{ $t('CTDashboardView.codelist_mean_count') }} <span class="font-weight-bold">{{ stats.codelistChangePercentage }}%</span><br>
              {{ $t('CTDashboardView.term_mean_count') }} <span class="font-weight-bold">{{ stats.termChangePercentage }}%</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col sm="12" lg="4">
        <v-card class="fixed-height" flat>
          <v-card-title>{{ $t('CTDashboardView.codelist_chart_title') }}</v-card-title>
          <v-card-text>
            <bar-chart
              :chart-data="codelistEvolutionData"
              :options="chartOptions"
              :styles="chartStyles"
              />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col sm="12" lg="4">
        <v-card class="fixed-height" flat>
          <v-card-title>{{ $t('CTDashboardView.term_chart_title') }}</v-card-title>
          <v-card-text>
            <bar-chart
              :chart-data="termEvolutionData"
              :options="chartOptions"
              :styles="chartStyles"
              />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12">
        <v-card flat>
          <v-card-title>{{ $t('CTDashboardView.table_title') }}</v-card-title>
          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="stats.latestAddedCodelists"
              hide-default-footer
              >
              <template v-slot:item.name.templateParameter="{ item }">
                {{ item.name.templateParameter|yesno }}
              </template>
              <template v-slot:item.name.status="{ item }">
                <status-chip :status="item.name.status" />
              </template>
              <template v-slot:item.name.startDate="{ item }">
                {{ item.name.startDate|date }}
              </template>
              <template v-slot:item.attributes.extensible="{ item }">
                {{ item.attributes.extensible|yesno }}
              </template>
              <template v-slot:item.attributes.status="{ item }">
                <status-chip :status="item.attributes.status" />
              </template>
              <template v-slot:item.attributes.startDate="{ item }">
                {{ item.attributes.startDate|date }}
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </template>
</div>

</template>

<script>
import controlledTerminology from '@/api/controlledTerminology'
import BarChart from '@/components/tools/BarChart'
import StatusChip from '@/components/tools/StatusChip'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    BarChart,
    StatusChip,
    HelpButton
  },
  data () {
    return {
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          yAxes: [
            {
              ticks: {
                beginAtZero: true
              }
            }]
        }
      },
      headers: [
        { text: this.$t('_global.library'), value: 'libraryName' },
        { text: this.$t('CTDashboardView.concept_id'), value: 'codelistUid' },
        { text: this.$t('CTDashboardView.sponsor_pref_name'), value: 'name.name' },
        { text: this.$t('CTDashboardView.template_parameter'), value: 'name.templateParameter' },
        { text: this.$t('CTDashboardView.name_status'), value: 'name.status' },
        { text: this.$t('_global.modified'), value: 'name.startDate' },
        { text: this.$t('CTDashboardView.codelist_name'), value: 'attributes.name' },
        { text: this.$t('CTDashboardView.subm_value'), value: 'attributes.submissionValue' },
        { text: this.$t('CTDashboardView.extensible'), value: 'attributes.extensible' },
        { text: this.$t('CTDashboardView.codelist_status'), value: 'attributes.status' },
        { text: this.$t('_global.modified'), value: 'attributes.startDate' }
      ],
      stats: {}
    }
  },
  computed: {
    codelistEvolutionData () {
      return this.computeEvolutionData('codelist')
    },
    termEvolutionData () {
      return this.computeEvolutionData('term')
    },
    chartStyles () {
      return {
        position: 'relative'
      }
    }
  },
  mounted () {
    controlledTerminology.getStats().then(resp => {
      this.stats = resp.data
    })
  },
  methods: {
    getCodelistCount (name) {
      if (this.stats.codelistCounts) {
        const result = this.stats.codelistCounts.find(item => item.libraryName === name)
        if (result) {
          return result.count
        }
      }
      return '?'
    },
    getTermCount (name) {
      if (this.stats.termCounts) {
        const result = this.stats.termCounts.find(item => item.libraryName === name)
        if (result) {
          return result.count
        }
      }
      return '?'
    },
    computeEvolutionData (property) {
      const years = []
      const datasets = {
        added: { label: this.$t('CTDashboardView.added'), data: [], backgroundColor: '#193074' },
        updated: { label: this.$t('CTDashboardView.updated'), data: [], backgroundColor: '#3f9c35' },
        deleted: { label: this.$t('CTDashboardView.deleted'), data: [], backgroundColor: '#e6553f' }
      }

      this.stats[`${property}ChangeDetails`].sort((a, b) => {
        return b.year - a.year
      })
      this.stats[`${property}ChangeDetails`].forEach(item => {
        years.unshift(item.year)
        item.counts.forEach(count => {
          datasets[count.type].data.unshift(count.count)
        })
      })

      return {
        labels: years,
        datasets: [datasets.added, datasets.updated, datasets.deleted]
      }
    }
  }
}
</script>

<style scoped>
.fixed-height {
  height: 500px;
}
</style>
