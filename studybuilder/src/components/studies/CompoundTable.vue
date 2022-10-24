<template>
<div>
  <n-n-table
    :headers="headers"
    :items="studyCompounds"
    item-key="studyCompoundUid"
    export-object-label="StudyCompounds"
    :export-data-url="exportDataUrl"
    :column-data-resource="`study/${selectedStudy.uid}/study-compounds`"
    has-api
    :options.sync="options"
    :server-items-length="total"
    @filter="fetchCompounds"
    >
    <template v-slot:actions="">
      <v-btn
        data-cy="add-study-compound"
        fab
        small
        color="primary"
        @click.stop="showForm = true"
        :title="$t('StudyCompoundForm.add_title')"
        >
        <v-icon>
          mdi-plus
        </v-icon>
      </v-btn>
    </template>
    <template v-slot:item.compound.isSponsorCompound="{ item }">
      <template v-if="item.compound">
        {{ item.compound.isSponsorCompound|yesno }}
      </template>
    </template>
    <template v-slot:item.compound.isNameInn="{ item }">
      <template v-if="item.compound">
        {{ item.compound.isNameInn|yesno }}
      </template>
    </template>
    <template v-slot:item.halfLife="{ item }">
      <template v-if="item.compound && item.compound.halfLife">
        {{ item.compound.halfLife.value }} {{ item.compound.halfLife.unitLabel }}
      </template>
    </template>
    <template v-slot:item.substances="{ item }">
      <template v-if="item.compound">
        {{ item.compound.substances|substances }}
      </template>
    </template>
    <template v-slot:item.pharmacologicalClasses="{ item }">
      <template v-if="item.compound">
        {{ item.compound.substances|pharmacologicalClasses }}
      </template>
    </template>
    <template v-slot:item.lagTimes="{ item }">
      <template v-if="item.compound && item.compound.lagTimes">
        {{ item.compound.lagTimes|lagTimes }}
      </template>
    </template>
    <template v-slot:item.compoundAlias.isPreferredSynonym="{ item }">
      <template v-if="item.compoundAlias">
        {{ item.compoundAlias.isPreferredSynonym|yesno }}
      </template>
    </template>
    <template v-slot:item.strengthValue="{ item }">
      <template v-if="item.strengthValue">
        {{ item.strengthValue.value }} {{ item.strengthValue.unitLabel }}
      </template>
    </template>
    <template v-slot:item.actions="{ item }">
      <actions-menu :actions="actions" :item="item" />
    </template>
  </n-n-table>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
  <v-dialog
    v-model="showForm"
    persistent
    fullscreen
    content-class="fullscreen-dialog"
    >
    <compound-form
      @close="closeForm"
      :study-compound="selectedStudyCompound"
      />
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import ActionsMenu from '@/components/tools/ActionsMenu'
import CompoundForm from './CompoundForm'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import NNTable from '@/components/tools/NNTable'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    ActionsMenu,
    CompoundForm,
    ConfirmDialog,
    NNTable
  },
  computed: {
    ...mapGetters({
      nullValues: 'studiesGeneral/nullValues',
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyCompounds: 'studyCompounds/studyCompounds'
    }),
    exportDataUrl () {
      return `study/${this.selectedStudy.uid}/study-compounds`
    }
  },
  data () {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil',
          iconColor: 'primary',
          click: this.editStudyCompound
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete',
          iconColor: 'error',
          click: this.deleteStudyCompound
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history'
        }
      ],
      headers: [
        { text: '', value: 'actions', width: '5%' },
        { text: '#', value: 'order' },
        { text: this.$t('StudyCompoundTable.type_of_treatment'), value: 'typeOfTreatment.name' },
        { text: this.$t('StudyCompoundTable.reason_for_missing'), value: 'reasonForMissingNullValue.name' },
        { text: this.$t('StudyCompoundTable.compound'), value: 'compound.name' },
        { text: this.$t('StudyCompoundTable.sponsor_compound'), value: 'compound.isSponsorCompound' },
        { text: this.$t('StudyCompoundTable.is_name_inn'), value: 'compound.isNameInn' },
        { text: this.$t('StudyCompoundTable.substance'), value: 'substances' },
        { text: this.$t('StudyCompoundTable.pharma_class'), value: 'pharmacologicalClasses' },
        { text: this.$t('StudyCompoundTable.compound_alias'), value: 'compoundAlias.name' },
        { text: this.$t('StudyCompoundTable.preferred_alias'), value: 'compoundAlias.isPreferredSynonym' },
        { text: this.$t('StudyCompoundTable.strength'), value: 'strengthValue' },
        { text: this.$t('StudyCompoundTable.dosage_form'), value: 'dosageForm.name' },
        { text: this.$t('StudyCompoundTable.route_of_admin'), value: 'routeOfAdministration.name' },
        { text: this.$t('StudyCompoundTable.dispensed_in'), value: 'dispensedIn.name' },
        { text: this.$t('StudyCompoundTable.device'), value: 'device.name' },
        { text: this.$t('StudyCompoundTable.half_life'), value: 'halfLife' },
        { text: this.$t('StudyCompoundTable.lag_time'), value: 'lagTimes' },
        { text: this.$t('StudyCompoundTable.nnc_number_long'), value: 'nncLongNumber' },
        { text: this.$t('StudyCompoundTable.nnc_number_short'), value: 'nncShortNumber' },
        { text: this.$t('StudyCompoundTable.analyte_number'), value: 'analyteNumber' },
        { text: this.$t('StudyCompoundTable.compound_definition'), value: 'compound.definition' },
        { text: this.$t('StudyCompoundTable.alias_definition'), value: 'compoundAlias.definition' }
      ],
      selectedStudyCompound: null,
      showForm: false,
      total: 0,
      options: {}
    }
  },
  methods: {
    fetchCompounds (filters, sort, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        this.options, filters, sort, filtersUpdated)
      params.studyUid = this.selectedStudy.uid
      this.$store.dispatch('studyCompounds/fetchStudyCompounds', params).then(resp => {
        this.total = resp.data.total
      })
    },
    async deleteStudyCompound (studyCompound) {
      const options = { type: 'warning' }
      let msg
      if (studyCompound.compound) {
        const compound = studyCompound.compound.name
        const context = { compound }
        if (studyCompound.studyCompoundDosingCount) {
          context.compoundDosings = studyCompound.studyCompoundDosingCount
          msg = this.$t('StudyCompoundTable.confirm_delete_cascade', context)
        } else {
          msg = this.$t('StudyCompoundTable.confirm_delete', context)
        }
      } else {
        msg = this.$t('StudyCompoundTable.confirm_delete_na')
      }
      if (!await this.$refs.confirm.open(msg, options)) {
        return
      }
      this.$store.dispatch('studyCompounds/deleteStudyCompound', {
        studyUid: this.selectedStudy.uid,
        studyCompoundUid: studyCompound.studyCompoundUid
      }).then(resp => {
        bus.$emit('notification', { msg: this.$t('StudyCompoundTable.delete_compound_success') })
      })
    },
    editStudyCompound (studyCompound) {
      this.selectedStudyCompound = studyCompound
      this.showForm = true
    },
    closeForm () {
      this.showForm = false
      this.selectedStudyCompound = null
    }
  },
  mounted () {
    this.fetchCompounds()
  },
  watch: {
    options () {
      this.fetchCompounds()
    }
  }
}
</script>
