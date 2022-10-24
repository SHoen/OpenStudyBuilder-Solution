<template>
  <div style="overflow-x: auto">
    <v-skeleton-loader
      v-if="studyCompounds__Loading"
      class="mx-auto"
      max-width="800px"
      type="table-heading, table-thead, table-tbody"
      />
    <div v-if="!studyCompounds__Loading && !studyCompounds.length" class="mx-4 my-8">{{ $t('InterventionOverview.no_intervention_selected') }}</div>
    <table  v-if="!studyCompounds__Loading && studyCompounds.length" class="mt-4">
      <thead>
        <tr>
          <th class="no-border"></th>
          <th :colspan="cols">{{ $t('InterventionOverview.study_compounds') }}</th>
        </tr>
        <tr>
          <th>{{ $t('InterventionOverview.first_col_title') }}</th>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`header-${index}`">
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.name }}
            </template>
          </td>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ $t('InterventionOverview.type_of_treatment') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`tot-${index}`">
            {{ studyCompound.typeOfTreatment.name }}
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.reason_for_missing') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`rfm-${index}`">
            <template v-if="studyCompound.reasonForMissingNullValue">
              {{ studyCompound.reasonForMissingNullValue.name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.sponsor_compound') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`sc-${index}`">
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.isSponsorCompound|yesno }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_number_long') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`cnl-${index}`">
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.nncLongNumber }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_number_short') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`cns-${index}`">
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.nncShortNumber }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.analyte_number') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`aln-${index}`">
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.analyteNumber }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.is_inn') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`inn-${index}`">
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.isNameInn|yesno }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.substances') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`sub-${index}`" class="no-padding">
            <table class="no-border" v-if="studyCompound.compound">
              <tbody>
                <tr
                  v-for="(substance, subIndex) in studyCompound.compound.substances"
                  :key="`sub-${index}-${subIndex}`"
                  :class="{ 'border-top': subIndex > 0 }"
                  >
                  <td class="no-border half-size">{{ substance.substanceName }} ({{ substance.substanceUnii }})</td>
                  <td class="border-left half-size">{{ substance.pclassName }} ({{ substance.pclassId }})</td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_aliases') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`alias-${index}`" class="no-padding">
            <table v-if="studyCompound.compound" class="no-border">
              <tbody>
                <tr
                  v-for="(alias, aliasIndex) in compoundAliases[studyCompound.compound.uid]"
                  :key="`alias-${index}-${aliasIndex}`"
                  class="no-padding"
                  :class="{ 'border-top': aliasIndex > 0 }"
                  >
                  <td class="no-border">{{ alias.name }} ({{ alias.isPreferredSynonym|yesno }})</td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.strength') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`strength-${index}`">
            <template v-if="studyCompound.strengthValue">
              {{ studyCompound.strengthValue.value }} ({{ studyCompound.strengthValue.unitLabel }})
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.pharmaceutical_dosage_form') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`dosage-${index}`">
            <template v-if="studyCompound.dosageForm">
              {{ studyCompound.dosageForm.name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.route_of_admin') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`roa-${index}`">
            <template v-if="studyCompound.routeOfAdministration">
              {{ studyCompound.routeOfAdministration.name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.dispensed_in') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`dispensed-${index}`">
            <template v-if="studyCompound.dispensedIn">
              {{ studyCompound.dispensedIn.name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.delivery_device') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`device-${index}`">
            <template v-if="studyCompound.device">
              {{ studyCompound.device.name }}
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_dosing') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`dosing-${index}`" class="no-padding">
            <table class="no-border" v-if="compoundDosings[studyCompound.studyCompoundUid]">
              <tr
                v-for="(compoundDosing, dosingIndex) in compoundDosings[studyCompound.studyCompoundUid]"
                :key="`lg-${index}-${dosingIndex}`"
                :class="{ 'border-top': dosingIndex > 0 }"
                >
                <td class="no-border half-size">{{ compoundDosing.studyElement.name }}</td>
                <td class="border-left half-size">
                  <template v-if="compoundDosing.doseValue">
                    {{ compoundDosing.doseValue.value }} {{ compoundDosing.doseValue.unitLabel }}{{ compoundDosing.doseFrequency ? ',' : '' }}
                  </template>
                  <template v-if="compoundDosing.doseFrequency">
                    <template v-if="compoundDosing.doseValue">{{ compoundDosing.doseFrequency.name }}</template>
                    <template v-else>{{ compoundDosing.doseFrequency.name }}</template>
                  </template>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.half_life') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`hl-${index}`">
            <template v-if="studyCompound.compound && studyCompound.compound.halfLife">
              {{ studyCompound.compound.halfLife.value }} ({{ studyCompound.compound.halfLife.unitLabel }})
            </template>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.lag_time') }}</td>
          <td v-for="(studyCompound, lgIndex) in studyCompounds" :key="`lg-${lgIndex}`" class="no-padding">
            <table class="no-border" v-if="studyCompound.compound && studyCompound.compound.lagTimes">
              <tr
                v-for="(lagTime, index) in studyCompound.compound.lagTimes"
                :key="`lg-${lgIndex}-${index}`"
                :class="{ 'border-top': index > 0 }"
                >
                <td class="no-border half-size">{{ lagTime.value }} ({{ lagTime.unitLabel }})</td>
                <td class="border-left half-size">{{ lagTime.sdtmDomainLabel }}</td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td>{{ $t('InterventionOverview.compound_def') }}</td>
          <td v-for="(studyCompound, index) in studyCompounds" :key="`def-${index}`">
            <template v-if="studyCompound.compound">
              {{ studyCompound.compound.definition }}
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import compoundAliases from '@/api/concepts/compoundAliases'
import { mapGetters } from 'vuex'

export default {
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyCompounds: 'studyCompounds/studyCompounds',
      studyCompounds__Loading: 'studyCompounds/studyCompounds__Loading',
      compoundDosings: 'studyCompounds/getStudyCompoundDosingsByStudyCompound'
    }),
    cols () {
      return this.studyCompounds.length ? this.studyCompounds.length : 1
    }
  },
  data () {
    return {
      compoundAliases: {}
    }
  },
  methods: {
    getCompoundAliases (compoundUid) {
      const params = {
        filters: {
          compoundUid: { v: [compoundUid], op: 'eq' }
        }
      }
      compoundAliases.getFiltered(params).then(resp => {
        this.$set(this.compoundAliases, compoundUid, resp.data.items)
      })
    },
    getAllCompoundAliases () {
      for (const studyCompound of this.studyCompounds) {
        if (!studyCompound.compound || this.compoundAliases[studyCompound.compound.uid] !== undefined) {
          continue
        }
        this.$set(this.compoundAliases, studyCompound.compound.uid, [])
        this.getCompoundAliases(studyCompound.compound.uid)
      }
    }
  },
  mounted () {
    this.$store.dispatch('studyCompounds/fetchStudyCompounds', { studyUid: this.selectedStudy.uid }).then(resp => {
      this.getAllCompoundAliases()
    })
    this.$store.dispatch('studyCompounds/fetchStudyCompoundDosings', { studyUid: this.selectedStudy.uid })
  },
  watch: {
    studyCompounds (value) {
      this.getAllCompoundAliases()
    }
  }
}
</script>

<style scoped lang="scss">
table {
  width: 100%;
  text-align: left;

  border-spacing: 0px;
  border-collapse: collapse;
}
.no-border {
  border: 0 !important;
}
.border-left {
  border: 0;
  border-left: 1px solid black;
}
.border-top {
  border: 0;
  border-top: 1px solid black;
}
.no-padding {
  padding: 0;
}
.half-size {
  width: 50%;
}
tr {
  padding: 4px;
}
td, th {
  border: 1px solid black;
  padding: 4px;
}
</style>
