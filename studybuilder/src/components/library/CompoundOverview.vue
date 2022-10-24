<template>
<v-card elevation="0" class="rounded-0">
  <v-card-text>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.sponsor_compound') }}
      </v-col>
      <v-col cols="2">
        {{ compound.isSponsorCompound|yesno }}
      </v-col>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.is_name_inn') }}
      </v-col>
      <v-col cols="2">
        {{ compound.isNameInn|yesno }}
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.nnc_number_long') }}
      </v-col>
      <v-col cols="2">
        {{ compound.nncLongNumber }}
      </v-col>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.nnc_number_short') }}
      </v-col>
      <v-col cols="2">
        {{ compound.nncShortNumber }}
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.analyte_number') }}
      </v-col>
      <v-col cols="2">
        {{ compound.analyteNumber }}
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.compound_aliases') }}
      </v-col>
      <v-col cols="6">
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr class="text-left">
                <th>{{ $t('CompoundOverview.compound_alias') }}</th>
                <th>{{ $t('_global.definition') }}</th>
                <th>{{ $t('CompoundOverview.preferred_alias') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="alias in compoundAliases" :key="alias.uid">
                <td>{{ alias.name }}</td>
                <td>{{ alias.definition }}</td>
                <td>{{ alias.isPreferredSynonym|yesno }}</td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('_global.definition') }}
      </v-col>
      <v-col cols="10">
        <div v-html="getHtmlLineBreaks(compound.definition)"></div>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.brand_name') }}
      </v-col>
      <v-col cols="10">
        <p v-for="brand in compound.brands" :key="brand.uid">
          {{ brand.name }}
        </p>
      </v-col>
    </v-row>
    <div class="my-4 py-4 substance" v-for="substance in compound.substances" :key="substance.substanceTermUid">
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.substance_name') }}
        </v-col>
        <v-col cols="2">
          {{ substance.substanceName }}
        </v-col>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.unii') }}
        </v-col>
        <v-col cols="2">
          {{ substance.substanceUnii }}
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.pharma_class') }}
        </v-col>
        <v-col cols="2">
          {{ substance.pclassName }}
        </v-col>
        <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.med_rt') }}
        </v-col>
        <v-col cols="2">
          {{ substance.pclassId }}
        </v-col>
      </v-row>
    </div>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.dose') }}
      </v-col>
      <v-col cols="6">
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr class="text-left">
                <th>{{ $t('CompoundOverview.value') }}</th>
                <th>{{ $t('CompoundOverview.unit') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="dose in compound.doseValues" :key="dose.uid">
                <td>{{ dose.value }}</td>
                <td>{{ dose.unitLabel }}</td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.strength') }}
      </v-col>
      <v-col cols="6">
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr class="text-left">
                <th>{{ $t('CompoundOverview.value') }}</th>
                <th>{{ $t('CompoundOverview.unit') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="strength in compound.strengthValues" :key="strength.uid">
                <td>{{ strength.value }}</td>
                <td>{{ strength.unitLabel }}</td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.dosing_freq') }}
      </v-col>
      <v-col cols="10">
        <p v-for="doseFreq in compound.doseFrequencies" :key="doseFreq.termUid">
          {{ doseFreq.name }}
        </p>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.route_of_admin') }}
      </v-col>
      <v-col cols="10">
        <p v-for="route in compound.routesOfAdministration" :key="route.termUid">
          {{ route.name }}
        </p>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.dosage_form') }}
      </v-col>
      <v-col cols="10">
        <p v-for="dosageForm in compound.dosageForms" :key="dosageForm.termUid">
          {{ dosageForm.name }}
        </p>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.dispensed_in') }}
      </v-col>
      <v-col cols="10">
        <p v-for="dispenser in compound.dispensers" :key="dispenser.termUid">
          {{ dispenser.name }}
        </p>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.device') }}
      </v-col>
      <v-col cols="10">
        <p v-for="device in compound.deliveryDevices" :key="device.termUid">
          {{ device.name }}
        </p>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
          {{ $t('CompoundOverview.half_life') }}
      </v-col>
      <v-col cols="2">
        {{ compound.halfLife ? compound.halfLife.value : "" }}
      </v-col>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.unit') }}
      </v-col>
      <v-col cols="2">
        {{ compound.halfLife ? compound.halfLife.unitLabel : "" }}
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2" class="font-weight-bold">
        {{ $t('CompoundOverview.lag_time') }}
      </v-col>
      <v-col cols="6">
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr class="text-left">
                <th>{{ $t('CompoundOverview.sdtm_domain') }}</th>
                <th>{{ $t('CompoundOverview.value') }}</th>
                <th>{{ $t('CompoundOverview.unit') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lagTime in compound.lagTimes" :key="lagTime.uid">
                <td>{{ lagTime.sdtmDomainLabel }}</td>
                <td>{{ lagTime.value }}</td>
                <td>{{ lagTime.unitLabel }}</td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-col>
    </v-row>

  </v-card-text>
</v-card>
</template>

<script>
import compoundAliases from '@/api/concepts/compoundAliases'

export default {
  props: {
    compound: Object
  },
  data () {
    return {
      compoundAliases: []
    }
  },
  watch: {
    compound (value) {
      const params = {
        filters: {
          compoundUid: { v: [value.uid] }
        }
      }
      compoundAliases.getFiltered(params).then(resp => {
        this.compoundAliases = resp.data.items
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.substance {
  border-bottom: 1px solid var(--v-greyBackground-base);
  border-top: 1px solid var(--v-greyBackground-base);
}
</style>
