<template>
  <v-card color="dfltBackground">
    <v-card-actions>
      <v-card-title class="dialog-about-title">
      {{ $t('About.title') }}
    </v-card-title>
      <v-spacer></v-spacer>
      <v-btn class="secondary-btn" color="white" @click="$emit('close')">
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
    <v-card-text>
      <p>{{ $t('About.components_list') }} {{ $config.STUDYBUILDER_VERSION }}</p>
      <p>{{ $t('About.header') }}</p>
      <v-simple-table>
        <thead>
          <tr>
            <th>{{ $t('About.component') }}</th>
            <th>{{ $t('About.description') }}</th>
            <th>{{ $t('About.build_number') }}</th>
            <th>{{ $t('About.license') }}</th>
            <th>{{ $t('About.sbom') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="component in sbComponents" :key="component.name">
            <td>{{ component.name }}</td>
            <td>{{ component.description }}</td>
            <td>{{ component.build_number }}</td>
            <td>
                <v-btn v-if="component.license_md" text @click="showLicenseText(component.license_md, component.name)">
                  {{ $t('_global.view') }}
                </v-btn>
            </td>
            <td>
                <v-btn v-if="component.sbom_md" text @click="showLicenseText(component.sbom_md, component.name)">
                  {{ $t('_global.view') }}
                </v-btn>
            </td>
          </tr>
        </tbody>
      </v-simple-table>
    </v-card-text>
    <v-dialog scrollable v-model="showLicense" max-width="800">
      <about-license :rawMarkdown='licenseText' :title='licenseTitle' @close="showLicense = false" />
    </v-dialog>
  </v-card>
</template>

<script>
import system from '@/api/system'
import axios from 'axios'
import AboutLicense from './AboutLicense.vue'

const sboms = {}
const licenses = {}
let url = ''
if (process.env.NODE_ENV === 'development') {
  url = '/'
} else {
  url = `https://${location.host}/`
}
try {
  axios.get(url + 'LICENSE-studybuilder.md').then(resp => {
    licenses.studyBuilder = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'sbom-studybuilder.md').then(resp => {
    sboms.studyBuilder = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'sbom-documentation-portal.md').then(resp => {
    sboms.documentation = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'LICENSE-documentation-portal.md').then(resp => {
    licenses.documentation = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'sbom-clinical-mdr-api.md').then(resp => {
    sboms.api = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'LICENSE-clinical-mdr-api.md').then(resp => {
    licenses.api = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'sbom-data-import.md').then(resp => {
    sboms.dataImport = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'LICENSE-data-import.md').then(resp => {
    licenses.dataImport = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'sbom-mdr-standards-import.md').then(resp => {
    sboms.standardsImport = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'LICENSE-mdr-standards-import.md').then(resp => {
    licenses.standardsImport = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'sbom-neo4j-mdr-db.md').then(resp => {
    sboms.mdrDb = resp.data
  })
} catch (err) {}
try {
  axios.get(url + 'LICENSE-neo4j-mdr-db.md').then(resp => {
    licenses.mdrDb = resp.data
  })
} catch (err) {}

export default {
  beforeCreate () {
    this.licenses = licenses
    this.sboms = sboms
  },
  components: {
    AboutLicense
  },
  data () {
    return {
      licenseText: null,
      showLicense: false,
      sbComponents: [
        {
          name: this.$t('About.studybuilder'),
          description: this.$t('About.studybuilder_description'),
          build_number: this.$config.FRONTEND_BUILD_NUMBER,
          license_md: this.licenses.studyBuilder,
          sbom_md: this.sboms.studyBuilder
        },
        {
          name: this.$t('About.documentation-portal'),
          description: this.$t('About.documentation-portal_description'),
          build_number: this.$config.DOCUMENTATION_PORTAL_BUILD_NUMBER,
          license_md: this.licenses.documentation,
          sbom_md: this.sboms.documentation
        },
        {
          name: this.$t('About.clinical-mdr-api'),
          description: this.$t('About.clinical-mdr-api_description'),
          build_number: this.$config.API_BUILD_NUMBER,
          license_md: this.licenses.api,
          sbom_md: this.sboms.api
        },
        {
          name: this.$t('About.database'),
          description: this.$t('About.db_description')
        },
        {
          name: this.$t('About.data-import'),
          description: this.$t('About.data-import_description'),
          build_number: this.$config.DATA_IMPORT_BUILD_NUMBER,
          license_md: this.licenses.dataImport,
          sbom_md: this.sboms.dataImport
        },
        {
          name: this.$t('About.mdr-standards-import'),
          description: this.$t('About.mdr-standards-import_description'),
          build_number: this.$config.STANDARDS_IMPORT_BUILD_NUMBER,
          license_md: this.licenses.standardsImport,
          sbom_md: this.sboms.standardsImport
        },
        {
          name: this.$t('About.neo4j-mdr-db'),
          description: this.$t('About.neo4j-mdr-db_description'),
          build_number: this.$config.NEO4J_MDR_BUILD_NUMBER,
          license_md: this.licenses.mdrDb,
          sbom_md: this.sboms.mdrDb
        }
      ]
    }
  },
  mounted () {
    system.getInformation().then(response => {
      this.$set(this.sbComponents[3], 'build_number', response.data.db_version)
    })
  },
  methods: {
    showLicenseText (text, title) {
      this.licenseText = text
      this.showLicense = true
      this.licenseTitle = title
    }
  }
}
</script>
