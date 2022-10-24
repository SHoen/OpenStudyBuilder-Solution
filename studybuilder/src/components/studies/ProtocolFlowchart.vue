<template>
<div class="pa-4">
  <div class="mt-6 d-flex align-center">
    <span class="text-h6">{{ $t('ProtocolFlowchart.title') }}</span>
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
        {{ $t('ProtocolFlowchart.download_docx') }}
      </v-btn>
    </div>
  </div>
  <div class="mt-4" v-html="protocolFlowchart" id="protocolFlowchart"></div>
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
      protocolFlowchart: '',
      loadingMessage: ''
    }
  },
  methods: {
    updateFlowchart () {
      this.loadingMessage = this.$t('ProtocolFlowchart.loading')
      study.getStudyProtocolFlowchartHtml(this.studyUid).then(resp => {
        this.protocolFlowchart = resp.data
      }).then(this.finally).catch(this.finally)
    },
    downloadDocx () {
      this.loadingMessage = this.$t('ProtocolFlowchart.downloading')
      study.getStudyProtocolFlowchartDocx(this.studyUid).then(response => {
        const blob = new Blob([response.data], {
          type: response.headers['content-type'] ||
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        const fileName = `${this.studyUid} flowchart.docx`
        exportLoader.generateDownload(blob, fileName)
      }).then(this.finally).catch(this.finally)
    },
    finally (error) {
      this.loadingMessage = ''
      if (error) throw error
    }
  },
  mounted () {
    this.updateFlowchart()
  },
  watch: {
    update (newVal, oldVal) {
      if (newVal !== oldVal) this.updateFlowchart()
    }
  }
}
</script>

<style lang="scss">
#ProtocolFlowchartTable {
  width: 100%;
  border-collapse: collapse;
  table-layout: auto;
  resize: both;

  &, & TH, & TD {
    border: 1px solid #ebe8e5;
    padding: 1px 3px;
  }

  & THEAD {
    background-color: #ebe8e5;

    & TH {
      border-color: white;
    }

    & .header1 TH:nth-child(n+2) {
      writing-mode: vertical-rl;
      vertical-align: bottom;
    }

    & TH:first-child {
      text-align: left;
    }
  }

  & TBODY {
    & TH {
      text-align: left;
      font-weight: normal;
    }

    & TR TD:nth-child(n+2) {
      text-align: center;
      vertical-align: middle;
    }

    & .fchGroup {
      text-transform: uppercase;
      background-color: #b1d5f2;
      TH {
        font-weight: bold;
      }
    }

    & .group {
      background-color: #d8eaf8;
      TH {
        font-weight: bold;
      }
    }

    & .subGroup {
      TH {
        font-weight: bold;
        padding-left: 1em;
      }
    }

    & .activity {
      TH {
        padding-left: 1em;
      }
    }
  }
}
</style>
