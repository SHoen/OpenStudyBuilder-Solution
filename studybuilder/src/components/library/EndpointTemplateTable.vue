<template>
<studybuilder-template-table
  ref="table"
  :url-prefix="urlPrefix"
  translation-type="EndpointTemplateTable"
  object-type="endpointTemplates"
  :headers="headers"
  has-api
  column-data-resource="endpoint-templates"
  fullscreen-form
  >
  <template v-slot:editform="{ closeForm, selectedObject, filter, updateTemplate }">
    <endpoint-template-form
      @close="closeForm"
      @templateAdded="filter()"
      @templateUpdated="updateTemplate(arguments[0], 'Draft')"
      :template="selectedObject"
      />
  </template>
  <template v-slot:item.categories.name.sponsorPreferredName="{ item }">
    <template v-if="item.categories">
      {{ item.categories|terms }}
    </template>
    <template v-else>
      {{ $t('_global.not_applicable_long') }}
    </template>
  </template>
  <template v-slot:item.subCategories.name.sponsorPreferredName="{ item }">
    <template v-if="item.subCategories">
      {{ item.subCategories|terms }}
    </template>
    <template v-else>
      {{ $t('_global.not_applicable_long') }}
    </template>
  </template>
  <template v-slot:indexingDialog="{ closeDialog, template }">
    <template-indexing-dialog
      @close="closeDialog"
      @updated="refreshTable"
      :template="template"
      :prepare-payload-func="prepareIndexingPayload"
      :url-prefix="urlPrefix"
      >
      <template v-slot:form="{ form }">
        <endpoint-template-indexing-form
          ref="indexingForm"
          :form="form"
          :template="template"
          />
      </template>
    </template-indexing-dialog>
  </template>
</studybuilder-template-table>
</template>

<script>
import EndpointTemplateForm from '@/components/library/EndpointTemplateForm'
import EndpointTemplateIndexingForm from './EndpointTemplateIndexingForm'
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable'
import TemplateIndexingDialog from './TemplateIndexingDialog'

export default {
  components: {
    EndpointTemplateForm,
    EndpointTemplateIndexingForm,
    StudybuilderTemplateTable,
    TemplateIndexingDialog
  },
  data () {
    return {
      headers: [
        {
          text: '',
          value: 'actions',
          sortable: false,
          width: '5%'
        },
        { text: this.$t('_global.indications'), value: 'indications.name' },
        { text: this.$t('EndpointTemplateTable.endpoint_cat'), value: 'categories.name.sponsorPreferredName' },
        { text: this.$t('EndpointTemplateTable.endpoint_sub_cat'), value: 'subCategories.name.sponsorPreferredName' },
        { text: this.$t('_global.template'), value: 'name', width: '30%' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' }
      ],
      urlPrefix: '/endpoint-templates'
    }
  },
  methods: {
    prepareIndexingPayload (form) {
      return this.$refs.indexingForm.preparePayload(form)
    },
    refreshTable () {
      this.$refs.table.$refs.sponsorTable.filter()
    }
  }
}
</script>
