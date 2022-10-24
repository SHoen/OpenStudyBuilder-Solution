<template>
  <div>
    <v-app-bar
      flat
      color="#e5e5e5"
      class="mt-2"
      style="height: 60px"
      >
      <v-row class="mt-2" v-if="doc === ''">
        <v-col cols="3">
          <v-select
            v-model="params.targetUid"
            :items="templates"
            :label="$t('OdmViewer.template')"
            dense
            clearable
            class="mt-2"
            item-text="name"
            item-value="uid">
          </v-select>
        </v-col>
        <v-col cols="5">
          <v-row>
            <v-radio-group
              v-model="params.stylesheet"
              :label="$t('OdmViewer.stylesheet')"
              row
              class="mt-4">
              <v-radio :label="$t('OdmViewer.blank')" value="odm_template_blankcrf.xsl" />
              <v-radio :label="$t('OdmViewer.sdtm')" value="odm_template_sdtmcrf.xsl" />
            </v-radio-group>
              <v-btn
                class="mt-4"
                dark
                small
                color="primary"
                :label="$t('_global.load')"
                @click="loadXml"
                v-show="params.targetUid && params.stylesheet">
                {{ $t('OdmViewer.load')}}
              </v-btn>
            </v-row>
        </v-col>
      </v-row>
      <v-row class="mt-0" v-else>
        <v-btn
          class="ml-2 mt-1"
          dark
          small
          color="primary"
          :label="$t('_global.load')"
          @click="clearXml"
          v-show="params.targetUid && params.stylesheet">
          {{ $t('OdmViewer.load_another')}}
        </v-btn>
        <v-btn
          fab
          small
          v-show="doc !== ''"
          color="nnGreen1"
          class="ml-4 white--text"
          :title="$t('DataTableExportButton.export_xml')"
          @click="downloadXml"
          :loading="downloadLoadingXml"
          >
          <v-icon >mdi-download</v-icon>
        </v-btn>
        <v-btn
          fab
          small
          v-show="doc !== ''"
          color="nnGreen1"
          class="ml-4 white--text"
          :title="$t('DataTableExportButton.export_html')"
          @click="downloadHtml"
          :loading="downloadLoadingHtml"
          >
          <v-icon>mdi-file-document</v-icon>
        </v-btn>
      </v-row>
    </v-app-bar>
    <div v-show="loading">
      <v-row align="center"
        justify="center"
        style="text-align: -webkit-center">
        <v-col cols="12" sm="4">
          <div class="text-h5">{{$t('OdmViewer.loading_message')}}</div>
          <v-progress-circular
            color="primary"
            indeterminate
            size="128"
            class="ml-4"
            />
        </v-col>
      </v-row>
    </div>
    <div v-html="doc"/>
  </div>
</template>

<script>
import crfs from '@/api/crfs'
import axios from 'axios'
import statuses from '@/constants/statuses'
import exportLoader from '@/utils/exportLoader'
import { DateTime } from 'luxon'

export default {
  components: {
  },
  data () {
    return {
      templates: [],
      uri: '',
      xml: '',
      doc: '',
      params: {
        exportTo: 'v1'
      },
      loading: false,
      downloadLoadingXml: false,
      downloadLoadingHtml: false
    }
  },
  mounted () {
    crfs.get('templates').then((resp) => {
      this.templates = resp.data.items.filter(this.isFinal)
    })
  },
  methods: {
    isFinal (item) {
      return item.status === statuses.FINAL
    },
    loadXml () {
      this.doc = ''
      this.loading = true
      this.params.targetType = 'template'
      let url = ''
      if (process.env.NODE_ENV === 'development') {
        url = `/${this.params.stylesheet}`
      } else {
        url = `https://${location.host}/${this.params.stylesheet}`
      }
      crfs.getXml(this.params).then(resp => {
        this.xml = resp.data
        const xsltProcessor = new XSLTProcessor()
        axios.get(url).then(resp => {
          const parser = new DOMParser()
          const xmlDoc = parser.parseFromString(resp.data, 'text/xml')
          xsltProcessor.importStylesheet(xmlDoc)
          this.doc = new XMLSerializer().serializeToString(xsltProcessor.transformToDocument(this.xml))
          this.loading = false
        })
      })
    },
    downloadHtml () {
      this.downloadLoadingHtml = true
      const blob = new Blob([this.doc], { type: 'text/html' })
      const stylesheet = this.params.stylesheet === 'odm_template_sdtmcrf.xsl' ? '_sdtm_crf_' : '_blank_crf_'
      const templateName = this.templates.filter(el => el.uid === this.params.targetUid)[0].name
      const fileName = `${templateName + stylesheet + DateTime.local().toFormat('yyyy-MM-dd HH:mm')}`
      exportLoader.generateDownload(blob, fileName)
      this.downloadLoadingHtml = false
    },
    downloadXml () {
      this.downloadLoadingXml = true
      crfs.getXmlToDownload(this.params).then(resp => {
        const blob = new Blob([resp.data], { type: 'text/xml' })
        const stylesheet = this.params.stylesheet === 'odm_template_sdtmcrf.xsl' ? '_sdtm_crf_' : '_blank_crf_'
        const templateName = this.templates.filter(el => el.uid === this.params.targetUid)[0].name
        const fileName = `${templateName + stylesheet + DateTime.local().toFormat('yyyy-MM-dd HH:mm')}`
        exportLoader.generateDownload(blob, fileName)
        this.downloadLoadingXml = false
      })
    },
    clearXml () {
      this.doc = ''
    }
  }
}
</script>
