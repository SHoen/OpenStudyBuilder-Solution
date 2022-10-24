<template>
<studybuilder-template-table
  ref="table"
  :url-prefix="urlPrefix"
  translation-type="ObjectiveTemplateTable"
  object-type="objectiveTemplates"
  :headers="headers"
  has-api
  column-data-resource="objective-templates"
  fullscreen-form
  >
  <template v-slot:editform="{ closeForm, selectedObject, filter, updateTemplate }">
    <objective-template-form
      @close="closeForm"
      @templateAdded="filter()"
      @templateUpdated="updateTemplate(arguments[0], 'Draft')"
      :template="selectedObject"
      />
  </template>
  <template v-slot:item.confirmatoryTesting="{ item }">
    <template v-if="item.defaultParameterValuesSet === undefined">
      <template v-if="item.confirmatoryTesting !== null">
        {{ item.confirmatoryTesting|yesno }}
      </template>
      <template v-else>
        {{ $t('_global.not_applicable_long') }}
      </template>
    </template>
  </template>
  <template v-slot:item.categories.name.sponsorPreferredName="{ item }">
    <template v-if="item.defaultParameterValuesSet === undefined">
      <template v-if="item.categories">
        {{ item.categories|terms }}
      </template>
      <template v-else>
        {{ $t('_global.not_applicable_long') }}
      </template>
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
        <objective-template-indexing-form
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
import ObjectiveTemplateForm from '@/components/library/ObjectiveTemplateForm'
import ObjectiveTemplateIndexingForm from './ObjectiveTemplateIndexingForm'
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable'
import TemplateIndexingDialog from './TemplateIndexingDialog'

export default {
  components: {
    ObjectiveTemplateForm,
    ObjectiveTemplateIndexingForm,
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
        { text: this.$t('ObjectiveTemplateTable.objective_cat'), value: 'categories.name.sponsorPreferredName' },
        { text: this.$t('ObjectiveTemplateTable.confirmatory_testing'), value: 'confirmatoryTesting' },
        { text: this.$t('_global.template'), value: 'name', width: '30%' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' }
      ],
      urlPrefix: '/objective-templates'
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
