<template>
<div class="pa-4">
  <div class="mt-6 d-flex align-center">
    <span class="text-h6">{{ $t('ProtocolInterventionsTable.title') }}</span>
    <v-spacer/>
    <span class="text-center font-italic">{{ loadingMessage }}</span>
    <v-spacer/>
    <div class="d-flex ml-4">
      <v-btn
        color="secondary"
        @click="downloadDocx($event)"
        class="ml-3"
        :disabled="Boolean(loadingMessage)"
      >
        {{ $t('ProtocolInterventionsTable.download_docx') }}
      </v-btn>
    </div>
  </div>
  <div class="mt-4" v-html="protocolInterventionsTable" id="ProtocolInterventions"></div>
</div>
</template>

<script>
import study from '@/api/study'
import exportLoader from '@/utils/exportLoader'

export default {
  props: {
    studyUid: String,
    update: Number
  },
  data () {
    return {
      protocolInterventionsTable: '',
      loadingMessage: ''
    }
  },
  methods: {
    updateTable () {
      this.loadingMessage = this.$t('ProtocolInterventionsTable.loading')
      study.getStudyProtocolInterventionsTableHtml(this.studyUid).then(resp => {
        this.protocolInterventionsTable = resp.data
      }).then(this.finally).catch(this.finally)
    },
    downloadDocx () {
      this.loadingMessage = this.$t('ProtocolInterventionsTable.downloading')
      study.getStudyProtocolInterventionsTableDocx(this.studyUid).then(response => {
        const blob = new Blob([response.data], {
          type: response.headers['content-type'] ||
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        const fileName = `${this.studyUid} interventions.docx`
        exportLoader.generateDownload(blob, fileName)
      }).then(this.finally).catch(this.finally)
    },
    finally (error) {
      this.loadingMessage = ''
      if (error) throw error
    }
  },
  mounted () {
    this.updateTable()
  },
  watch: {
    update (newVal, oldVal) {
      if (newVal !== oldVal) this.updateTable()
    }
  }
}
</script>

<style lang="scss">
#StudyInterventionsTable {
  width: 100%;
  table-layout: auto;
  resize: both;
  border-collapse: collapse;

  &, & TH, & TD {
    border: 1px solid #ebe8e5;
    padding: 1px 3px;
  }

  & THEAD {

    & TH {
      text-align: center;
      font-weight: bold;
    }

    & TH:first-child {
      text-align: left;
    }
  }

  & TBODY {
    & TH {
      text-align: left;
      font-weight: bold;
    }

    & TR TD {
      text-align: left;
    }

  }
}
</style>
