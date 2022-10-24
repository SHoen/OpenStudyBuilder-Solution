<template>
<v-card data-cy="version-history-window">
  <v-card-title>
    <span class="dialog-title">{{ $t('HistoryTable.title') }} {{ titleLabel }}</span><span v-if="item && item.name" class="ml-2 dialog-title">[{{ item.name }}]</span><span v-else-if="itemUid" class="ml-2 dialog-title">[{{ itemUid }}]</span>
    <v-spacer/>
    <data-table-export-button
      v-if="urlPrefix"
      :type="type"
      :dataUrl="`${urlPrefix}${itemUid}/versions`"
      />
  </v-card-title>
  <v-card-text>
    <v-data-table
      :headers="headers"
      :items="history"
      dense
      >
      <template v-slot:item="{ item }">
        <tr>
          <td v-for="(header, index)  in headers" v-bind:key="index">
             <div v-if="getHighlight(index, header, item)" class="blue lighten-4 difference">{{ getDisplay(item, header.value) }}</div>
             <span v-else>{{ getDisplay(item, header.value) }}</span>
          </td>
        </tr>
      </template>
    </v-data-table>
  </v-card-text>
  <v-card-actions>
    <div class="blue lighten-4 difference">{{ $t('HistoryTable.legend') }}</div>
    <v-spacer></v-spacer>
    <v-btn
      color="secondary"
      @click="close"
      >
      {{ $t('_global.close') }}
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
import { DateTime } from 'luxon'
import { mapGetters } from 'vuex'
import objectiveTemplates from '@/api/objectiveTemplates'
import endpointTemplates from '@/api/endpointTemplates'
import study from '@/api/study'
import timeframeTemplates from '@/api/timeframeTemplates'
import objectives from '@/api/objectives'
import endpoints from '@/api/endpoints'
import timeframes from '@/api/timeframes'
import controlledTerminology from '@/api/controlledTerminology'
import DataTableExportButton from '@/components/tools/DataTableExportButton'
import studyEpochs from '@/api/studyEpochs'
import _isEmpty from 'lodash/isEmpty'
import crfs from '@/api/crfs'
import compounds from '@/api/concepts/compounds'
import compoundAliases from '@/api/concepts/compoundAliases'
import arms from '@/api/arms'

export default {
  props: {
    item: Object,
    type: String,
    titleLabel: String,
    urlPrefix: String
  },
  components: {
    DataTableExportButton
  },
  data () {
    return {
      history: []
    }
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    itemUid () {
      if (this.item) {
        if (this.type === 'codelistSponsorValues') {
          return this.item.codelistUid
        }
        if (this.type === 'studyObjective' || this.type === 'studyEndpoint') {
          return null
        }
        return this.item.uid
      }
      return null
    },
    headers () {
      if (this.type === 'studyEpoch') {
        return [
          { text: this.$t('_global.uid'), value: 'uid' },
          { text: this.$t('_global.name'), value: 'epochName' },
          { text: this.$t('HistoryTable.change_description'), value: 'changeDescription' },
          { text: this.$t('_global.status'), value: 'status' },
          { text: this.$t('_global.order'), value: 'order' },
          { text: this.$t('_global.user'), value: 'userInitials' },
          { text: this.$t('HistoryTable.start_date'), value: 'creationDate' },
          { text: this.$t('HistoryTable.end_date'), value: 'modificationDate' }
        ]
      }
      if (this.type === 'studyVisit') {
        return [
          { text: this.$t('_global.uid'), value: 'uid' },
          { text: this.$t('_global.name'), value: 'name' },
          { text: this.$t('HistoryTable.change_description'), value: 'changeDescription' },
          { text: this.$t('_global.status'), value: 'status' },
          { text: this.$t('_global.order'), value: 'order' },
          { text: this.$t('_global.user'), value: 'userInitials' },
          { text: this.$t('HistoryTable.start_date'), value: 'creationDate' },
          { text: this.$t('HistoryTable.end_date'), value: 'modificationDate' }
        ]
      }
      if (this.type === 'studyActivity') {
        return [
          { text: '#', value: 'order' },
          { text: this.$t('StudyActivity.flowchart_group'), value: 'flowchartGroup.sponsorPreferredName' },
          { text: this.$t('StudyActivity.activity'), value: 'activity.name' },
          { text: this.$t('HistoryTable.change_description'), value: 'changeType' },
          { text: this.$t('_global.status'), value: 'status' },
          { text: this.$t('_global.user'), value: 'userInitials' },
          { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
          { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
        ]
      }
      if (this.type === 'studyEndpoint') {
        return [
          { text: this.$t('_global.endpoint'), value: 'endpoint.name' },
          { text: this.$t('_global.timeframe'), value: 'timeframe.name' },
          { text: this.$t('StudyEndpointsTable.endpoint_level'), value: 'endpointLevel.sponsorPreferredName' },
          { text: this.$t('StudyEndpointsTable.order'), value: 'order' },
          { text: this.$t('HistoryTable.change_description'), value: 'changeType' },
          { text: this.$t('_global.status'), value: 'status' },
          { text: this.$t('_global.user'), value: 'userInitials' },
          { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
          { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
        ]
      }
      if (this.type === 'studyCriteria') {
        return [
          { text: this.$t('EligibilityCriteriaTable.criteria'), value: 'criteria.name' },
          { text: this.$t('EligibilityCriteriaTable.guidance_text'), value: 'guidanceText' },
          { text: this.$t('_global.order'), value: 'order' },
          { text: this.$t('HistoryTable.change_description'), value: 'changeType' },
          { text: this.$t('_global.user'), value: 'userInitials' },
          { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
          { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
        ]
      }
      if (this.type === 'studyCompoundDosing') {
        return [
          { text: this.$t('StudyCompoundDosingTable.element'), value: 'studyElement.name' },
          { text: this.$t('StudyCompoundDosingTable.compound'), value: 'studyCompound.compound.name' },
          { text: this.$t('StudyCompoundDosingTable.dose_value'), value: 'doseValue' },
          { text: this.$t('StudyCompoundDosingTable.dose_frequency'), value: 'doseFrequency.name' },
          { text: this.$t('_global.user'), value: 'userInitials' },
          { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
          { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
        ]
      }
      if (this.type === 'studyArm') {
        return [
          { text: this.$t('_global.name'), value: 'name' },
          { text: this.$t('HistoryTable.short_name'), value: 'shortName' },
          { text: this.$t('HistoryTable.arm_type'), value: 'armType' },
          { text: this.$t('_global.order'), value: 'order' },
          { text: this.$t('_global.description'), value: 'description' },
          { text: this.$t('_global.user'), value: 'userInitials' },
          { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
          { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
        ]
      }
      if (this.type === 'studyBranch') {
        return [
          { text: this.$t('_global.name'), value: 'name' },
          { text: this.$t('HistoryTable.short_name'), value: 'shortName' },
          { text: this.$t('HistoryTable.branch_code'), value: 'code' },
          { text: this.$t('HistoryTable.planned_number'), value: 'numberOfSubjects' },
          { text: this.$t('HistoryTable.rand_group'), value: 'randomizationGroup' },
          { text: this.$t('_global.order'), value: 'order' },
          { text: this.$t('_global.description'), value: 'description' },
          { text: this.$t('_global.user'), value: 'userInitials' },
          { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
          { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
        ]
      }
      if (this.type === 'studyCohort') {
        return [
          { text: this.$t('_global.name'), value: 'name' },
          { text: this.$t('HistoryTable.short_name'), value: 'shortName' },
          { text: this.$t('HistoryTable.branch_code'), value: 'code' },
          { text: this.$t('HistoryTable.planned_number'), value: 'numberOfSubjects' },
          { text: this.$t('_global.order'), value: 'order' },
          { text: this.$t('_global.description'), value: 'description' },
          { text: this.$t('_global.user'), value: 'userInitials' },
          { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
          { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
        ]
      }
      if (this.type === 'studyElement') {
        return [
          { text: this.$t('_global.name'), value: 'name' },
          { text: this.$t('HistoryTable.short_name'), value: 'shortName' },
          { text: this.$t('HistoryTable.element_subtype'), value: 'elementSubType.sponsorPreferredName' },
          { text: this.$t('HistoryTable.start_rule'), value: 'startRule' },
          { text: this.$t('HistoryTable.end_rule'), value: 'endRule' },
          { text: this.$t('_global.order'), value: 'order' },
          { text: this.$t('_global.description'), value: 'description' },
          { text: this.$t('_global.user'), value: 'userInitials' },
          { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
          { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
        ]
      }
      return [
        { text: this.$t('_global.library'), value: 'libraryName' },
        { text: this.$t('_global.name'), value: 'name' },
        { text: this.$t('HistoryTable.change_description'), value: 'changeDescription' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' },
        { text: this.$t('_global.user'), value: 'userInitials' },
        { text: this.$t('HistoryTable.start_date'), value: 'startDate' },
        { text: this.$t('HistoryTable.end_date'), value: 'endDate' }
      ]
    }
  },
  methods: {
    close () {
      this.$emit('close')
    },
    /**
     * Fetch version history for given item uid.
     */
    async fetchHistory (item) {
      let resp
      if (!_isEmpty(item)) {
        if (this.type === 'objectiveTemplates') {
          resp = await objectiveTemplates.getVersions(item.uid)
        } else if (this.type === 'endpointTemplates') {
          resp = await endpointTemplates.getVersions(item.uid)
        } else if (this.type === 'objective') {
          resp = await objectives.getVersions(item.uid)
        } else if (this.type === 'timeframeTemplates') {
          resp = await timeframeTemplates.getVersions(item.uid)
        } else if (this.type === 'timeframe') {
          resp = await timeframes.getVersions(item.uid)
        } else if (this.type === 'studyObjective') {
          resp = await study.getStudyObjectiveAuditTrail(this.selectedStudy.uid, item.studyObjectiveUid)
        } else if (this.type === 'studyEndpoint') {
          resp = await study.getStudyEndpointAuditTrail(this.selectedStudy.uid, item.studyEndpointUid)
        } else if (this.type === 'codelistSponsorValues') {
          resp = await controlledTerminology.getCodelistNamesVersions(item.codelistUid)
        } else if (this.type === 'codelistAttributes') {
          resp = await controlledTerminology.getCodelistAttributesVersions(item.codelistUid)
        } else if (this.type === 'studyEpoch') {
          resp = await studyEpochs.getStudyEpochVersions(this.selectedStudy.uid, item.uid)
        } else if (this.type === 'studyVisit') {
          resp = await studyEpochs.getStudyVisitVersions(this.selectedStudy.uid, item.uid)
        } else if (this.type === 'studyActivity') {
          resp = await study.getStudyActivityAuditTrail(this.selectedStudy.uid, item.studyActivityUid)
        } else if (this.type === 'studyCriteria') {
          resp = await study.getStudyCriteriaAuditTrail(this.selectedStudy.uid, item.studyCriteriaUid)
        } else if (this.type === 'crfForm') {
          resp = await crfs.getFormAuditTrail(item.uid)
        } else if (this.type === 'crfGroup') {
          resp = await crfs.getGroupAuditTrail(item.uid)
        } else if (this.type === 'crfItem') {
          resp = await crfs.getItemAuditTrail(item.uid)
        } else if (this.type === 'compound') {
          resp = await compounds.getVersions(item.uid)
        } else if (this.type === 'compoundAlias') {
          resp = await compoundAliases.getVersions(item.uid)
        } else if (this.type === 'studyCompoundDosing') {
          resp = await study.getStudyCompoundDosingAuditTrail(this.selectedStudy.uid, item.studyCompoundDosingUid)
        } else if (this.type === 'studyArm') {
          resp = await studyEpochs.getStudyArmVersions(this.selectedStudy.uid, item.armUid)
        } else if (this.type === 'studyBranch') {
          resp = await studyEpochs.getStudyBranchVersions(this.selectedStudy.uid, item.branchArmUid)
        } else if (this.type === 'studyCohort') {
          resp = await arms.getStudyCohortVersions(this.selectedStudy.uid, item.cohortUid)
        } else if (this.type === 'studyElement') {
          resp = await arms.getStudyElementVersions(this.selectedStudy.uid, item.elementUid)
        } else {
          resp = await endpoints.getVersions(item.uid)
        }
        this.history = resp.data
      }
    },
    getHighlight (index, header, item) {
      if (item) {
        if (header.value.indexOf('Date') !== -1) {
          return false
        } else if (item.changes) {
          return item.changes[header.value]
        } else {
          return false
        }
      }
    },
    getDisplay (item, accessor) {
      const accessList = accessor.split('.')
      if (item) {
        let value = item
        for (const i in accessList) {
          const label = accessList[i]
          if (value) {
            value = value[label]
          }
        }
        if (accessor.indexOf('Date') !== -1) {
          if (value) {
            value = DateTime.fromISO(value).setLocale('en').toLocaleString(DateTime.DATETIME_MED)
          }
        }
        if (accessor.indexOf('armType') !== -1) {
          if (value) {
            value = value.sponsorPreferredName
          }
        }
        if (accessor === 'doseValue') {
          value = `${value.value} ${value.unitLabel}`
        }
        return value
      }
    }
  },
  mounted () {
    if ('item' in this && this.item) {
      this.fetchHistory(this.item)
    }
  },
  watch: {
    item: {
      handler (value) {
        if (value) {
          this.fetchHistory(value)
        }
      },
      immediate: true
    }
  }
}
</script>

<style scoped>
  .difference,
  .history-info {
    display: flex;
    justify-content: center;
    flex-direction: column;
    padding: 0 10px;
    border-radius: 12px;
    height: 60px;
    margin: 10px 0;
  }
</style>
