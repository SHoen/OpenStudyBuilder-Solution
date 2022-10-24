<template>
<div class="pa-4">
  <div class="mt-6 d-flex align-center">
    <span class="text-h6">{{ $t('ProtocolElementsObjectiveTable.title') }}</span>
    <v-spacer/>
    <span class="text-center font-italic">{{ loadingMessage }}</span>
    <v-spacer/>
    <div class="d-flex ml-4">
      <v-btn
        color="secondary"
        @click="downloadDocx()"
        class="ml-3"
        :disabled="Boolean(loadingMessage)"
      >
        {{ $t('ProtocolElementsObjectiveTable.download_docx') }}
      </v-btn>
    </div>
  </div>
  <table class="mt-4">
    <thead>
      <tr>
        <th width="40%">{{ $t('_global.objectives') }}</th>
        <th colspan="3">{{ $t('_global.endpoints') }}</th>
      </tr>
    </thead>
    <tbody>
      <!-- eslint-disable -->
      <template v-for="level in sortedObjectiveLevels">
        <template v-if="studyObjectivesPerLevel[level.termUid]">
          <tr class="section">
            <td>{{ level.sponsorPreferredName }}</td>
            <td>{{ $t('_global.title') }}</td>
            <td>{{ $t('_global.timeframe') }}</td>
            <td>{{ $t('_global.unit') }}</td>
          </tr>
          <template v-for="objective in studyObjectivesPerLevel[level.termUid]">
            <template v-if="Object.keys(objective.endpoints).length > 0">
              <template v-for="(levelEndpoints, index) in getSortedEndpoints(objective.endpoints)">
                <tr :key="objective.uid">
                  <td class="top-align" v-if="index === 0" :rowspan="getRowSpan(objective)" v-html="getObjectName(objective)"></td>
                  <td colspan="3" class="font-weight-bold">{{ levelEndpoints.level }}</td>
                </tr>
                <tr v-for="endpoint in levelEndpoints.endpoints" :key="endpoint.uid">
                  <td class="top-align" v-html="getObjectName(endpoint.endpoint)"></td>
                  <td class="top-align" v-if="endpoint.timeframe">{{ endpoint.timeframe.namePlain|stripBrackets }}</td>
                  <td v-else></td>
                  <td class="top-align">{{ displayUnits(endpoint.endpointUnits) }}</td>
                </tr>
              </template>
            </template>
            <template v-else>
              <tr :key="objective.uid">
                <td class="top-align" v-html="getObjectName(objective)"></td>
                <td colspan="3" class="font-weight-bold"></td>
              </tr>
            </template>
          </template>
        </template>
      </template>
      <!-- eslint-enable -->
    </tbody>
  </table>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import study from '@/api/study'
import exportLoader from '@/utils/exportLoader'

export default {
  computed: {
    ...mapGetters({
      allUnits: 'studiesGeneral/allUnits',
      selectedStudy: 'studiesGeneral/selectedStudy',
      sortedObjectiveLevels: 'studiesGeneral/sortedObjectiveLevels',
      sortedEndpointLevels: 'studiesGeneral/sortedEndpointLevels'
    })
  },
  data () {
    return {
      loadingMessage: '',
      notReadyForTransfer: false,
      studyObjectivesPerLevel: {}
    }
  },
  methods: {
    displayUnits (units) {
      const unitNames = units.units.map(unitUid => this.allUnits.find(unit => unit.uid === unitUid).name)
      if (unitNames.length > 1) {
        return (units.separator === ',') ? unitNames.join(`${units.separator} `) : unitNames.join(` ${units.separator} `)
      }
      return unitNames[0]
    },
    getRowSpan (objective) {
      let result = 0
      for (const level in objective.endpoints) {
        if (objective.endpoints[level].length > 0) {
          result += (1 + objective.endpoints[level].length)
        }
      }
      return result
    },
    /*
    ** Return endpoints sorted by levels
    */
    getSortedEndpoints (endpoints) {
      const result = []
      this.sortedEndpointLevels.forEach(level => {
        const termUid = level.termUid
        if (endpoints[termUid] === undefined) {
          return
        }
        const endpoint = endpoints[termUid][0]
        if (endpoint) {
          level = endpoint.endpointSubLevel || endpoint.endpointLevel
        }
        result.push({
          level: level.sponsorPreferredName,
          endpoints: endpoints[termUid]
        })
      })
      return result
    },
    getObjectName (objective) {
      return objective.name.replaceAll(/\[|\]/g, '')
    },
    downloadDocx () {
      this.loadingMessage = this.$t('ProtocolElementsObjectiveTable.downloading')
      study.getStudyObjectivesDocx(this.selectedStudy.uid).then(response => {
        const blob = new Blob([response.data], {
          type: response.headers['content-type'] ||
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        const fileName = `${this.selectedStudy.uid} objectives.docx`
        exportLoader.generateDownload(blob, fileName)
      }).then(this.finally).catch(this.finally)
    },
    finally (error) {
      this.loadingMessage = ''
      if (error) throw error
    }

  },
  mounted () {
    this.loadingMessage = this.$t('ProtocolElementsObjectiveTable.loading')
    this.$store.dispatch('studiesGeneral/fetchObjectiveLevels')
    this.$store.dispatch('studiesGeneral/fetchEndpointLevels')
    this.$store.dispatch('studiesGeneral/fetchAllUnits')
    study.getStudyObjectives(this.selectedStudy.uid).then(resp => {
      for (const studyObjective of resp.data.items) {
        const objectiveLevelUid = studyObjective.objectiveLevel.termUid
        if (this.studyObjectivesPerLevel[objectiveLevelUid] === undefined) {
          this.$set(this.studyObjectivesPerLevel, objectiveLevelUid, [])
        }
        const newEntry = {
          name: studyObjective.objective.name,
          endpoints: {}
        }
        this.studyObjectivesPerLevel[objectiveLevelUid].push(newEntry)
      }
      study.getStudyEndpoints(this.selectedStudy.uid).then(resp => {
        resp.data.items.forEach(studyEndpoint => {
          if (!studyEndpoint.studyObjective || !studyEndpoint.studyObjective.objectiveLevel) return
          const objectiveLevelUid = studyEndpoint.studyObjective.objectiveLevel.termUid
          const objArray = this.studyObjectivesPerLevel[objectiveLevelUid]
          const objEntry = objArray.find(item => item.name === studyEndpoint.studyObjective.objective.name)
          const endpointLevel = studyEndpoint.endpointLevel ? studyEndpoint.endpointLevel.termUid : ''
          if (objEntry.endpoints[endpointLevel] === undefined) {
            this.$set(objEntry.endpoints, endpointLevel, [])
          }
          objEntry.endpoints[endpointLevel].push(studyEndpoint)
        })
      }).then(this.finally).catch(this.finally)
    }).catch(this.finally)
  }
}
</script>

<style scoped lang="scss">
table {
  width: 100%;
  text-align: left;
  border: 1px solid black;
  border-spacing: 0px;
  border-collapse: collapse;
}
tr {
  padding: 4px;
  &.section {
    background-color: var(--v-greyBackground-base);
    font-weight: 600;
  }
}
td, th {
  border: 1px solid black;
  padding: 4px;
}
td.top-align {
  vertical-align: top;
}
</style>
