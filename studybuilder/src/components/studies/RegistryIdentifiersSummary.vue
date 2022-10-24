<template>
<study-metadata-summary
  :metadata="identifiers"
  :params="params"
  :first-col-label="$t('StudyRegistryIdentifiersSummary.registry_identifiers')"
  :fullscreen-form="false"
  form-max-width="1000px"
  >
  <template v-slot:form="{ closeHandler, openHandler }">
    <registry-identifiers-form
      :open="openHandler"
      @close="closeHandler"
      @updated="onIdentifiersUpdated"
      :identifiers="identifiers"
      />
  </template>
</study-metadata-summary>
</template>

<script>
import { mapGetters } from 'vuex'
import study from '@/api/study'
import RegistryIdentifiersForm from './RegistryIdentifiersForm'
import StudyMetadataSummary from './StudyMetadataSummary'

export default {
  components: {
    RegistryIdentifiersForm,
    StudyMetadataSummary
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      identifiers: {},
      params: [
        {
          label: this.$t('RegistryIdentifiersForm.ctgovid'),
          name: 'ctGovId',
          nullValueName: 'ctGovIdNullValueCode'
        },
        {
          label: this.$t('RegistryIdentifiersForm.eudractid'),
          name: 'eudractId',
          nullValueName: 'eudractIdNullValueCode'
        },
        {
          label: this.$t('RegistryIdentifiersForm.utn'),
          name: 'universalTrialNumberUTN',
          nullValueName: 'universalTrialNumberUTNNullValueCode'
        },
        {
          label: this.$t('RegistryIdentifiersForm.japic'),
          name: 'japaneseTrialRegistryIdJAPIC',
          nullValueName: 'japaneseTrialRegistryIdJAPICNullValueCode'
        },
        {
          label: this.$t('RegistryIdentifiersForm.ind'),
          name: 'investigationalNewDrugApplicationNumberIND',
          nullValueName: 'investigationalNewDrugApplicationNumberINDNullValueCode'
        }
      ]
    }
  },
  methods: {
    onIdentifiersUpdated (identifiers) {
      this.identifiers = identifiers
    }
  },
  mounted () {
    this.$store.dispatch('studiesGeneral/fetchNullValues')
    study.getStudy(this.selectedStudy.uid).then(resp => {
      this.identifiers = resp.data.currentMetadata.identificationMetadata.registryIdentifiers
    })
  }
}
</script>
