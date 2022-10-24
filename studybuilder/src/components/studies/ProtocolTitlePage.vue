<template>
<div>
  <div class="mt-6 d-flex align-center">
    <v-card-title class="text-h6">{{ $t('StudyProtocolElementsView.title_page') }}</v-card-title>
  </div>
  <v-data-table
    class="mt-2"
    :headers="headers"
    :items="items"
    hide-default-footer
    />
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import study from '@/api/study'

export default {
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      headers: [
        { text: this.$t('ProtocolTitlePage.title_page_elements'), value: 'label', width: '30%' },
        { text: this.$t('ProtocolTitlePage.values'), value: 'value' }
      ],
      items: []
    }
  },
  mounted () {
    study.getStudyProtocolTitle(this.selectedStudy.uid).then(resp => {
      this.items = [
        { label: this.$t('ProtocolTitlePage.protocol_title'), value: resp.data.studyTitle },
        { label: this.$t('ProtocolTitlePage.protocol_short_title'), value: resp.data.studyShortTitle },
        { label: this.$t('ProtocolTitlePage.substance_name'), value: resp.data.substanceName },
        { label: this.$t('ProtocolTitlePage.utn'), value: resp.data.universalTrialNumberUTN },
        { label: this.$t('ProtocolTitlePage.eudract_number'), value: resp.data.eudractId },
        { label: this.$t('ProtocolTitlePage.ind_number'), value: resp.data.indNumber },
        { label: this.$t('ProtocolTitlePage.study_phase'), value: resp.data.trialPhaseCode ? resp.data.trialPhaseCode.name : '' }
      ]
    })
  }
}
</script>
