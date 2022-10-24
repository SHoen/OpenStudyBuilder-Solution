<template>
<div class="pa-4">
  <div class="mt-6 d-flex align-center">
    <span class="text-h6">{{ $t('StudyProtocolElementsView.study_design') }}</span>
    <v-spacer/>
    <span class="text-center font-italic">{{ loadingMessage }}</span>
    <v-spacer/>
    <div class="d-flex ml-4">
      <v-btn
        color="secondary"
        @click="downloadSvg($event)"
        class="ml-3"
        :disabled="Boolean(loadingMessage)"
      >
        {{ $t('StudyProtocolElementsView.download') }}
      </v-btn>
    </div>
  </div>
  <div class="mt-4" v-html="studyDesignSVG" id="studyDesign"></div>
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
      studyDesignSVG: '',
      loadingMessage: ''
    }
  },
  methods: {
    updateSvg () {
      this.loadingMessage = this.$t('StudyProtocolElementsView.loading')
      study.getStudyDesignFigureSvg(this.studyUid).then(resp => {
        this.studyDesignSVG = resp.data
      }).then(this.finally).catch(this.finally)
    },
    downloadSvg () {
      this.loadingMessage = this.$t('StudyProtocolElementsView.downloading')
      study.getStudyDesignFigureSvgArray(this.studyUid).then(response => {
        const blob = new Blob([response.data], {
          type: response.headers['content-type'] || 'image/svg+xml'
        })
        const fileName = `${this.studyUid} design.svg`
        exportLoader.generateDownload(blob, fileName)
      }).then(this.finally).catch(this.finally)
    },
    finally (error) {
      this.loadingMessage = ''
      if (error) throw error
    }
  },
  mounted () {
    this.updateSvg()
  },
  watch: {
    update (newVal, oldVal) {
      if (newVal !== oldVal) this.updateSvg()
    }
  }
}
</script>
