<template>
<studybuilder-template-table
  ref="table"
  :url-prefix="urlPrefix"
  translation-type="CriteriaTemplateTable"
  object-type="criteriaTemplates"
  :headers="headers"
  :extra-filters-func="getExtraFilters"
  has-api
  column-data-resource="criteria-templates"
  fullscreen-form
  >
  <template v-slot:editform="{ closeForm, selectedObject, filter, updateTemplate }">
    <criteria-template-form
      :type="type"
      @close="closeForm"
      :template="selectedObject"
      @templateAdded="filter()"
      @templateUpdated="updateTemplate(arguments[0], 'Draft')"
      />
  </template>
  <template v-slot:item.guidanceText="{ item }">
    <div v-html="item.guidanceText" />
  </template>
  <template v-slot:item.categories="{ item }">
    <template v-if="item.categories">
      {{ item.categories|terms }}
    </template>
    <template v-else>
      {{ $t('_global.not_applicable_long') }}
    </template>
  </template>
  <template v-slot:item.subCategories="{ item }">
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
        <criteria-template-indexing-form
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
import terms from '@/api/controlledTerminology/terms'
import CriteriaTemplateForm from './CriteriaTemplateForm'
import CriteriaTemplateIndexingForm from './CriteriaTemplateIndexingForm'
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable'
import TemplateIndexingDialog from './TemplateIndexingDialog'

export default {
  props: {
    type: String
  },
  components: {
    CriteriaTemplateForm,
    CriteriaTemplateIndexingForm,
    StudybuilderTemplateTable,
    TemplateIndexingDialog
  },
  data () {
    return {
      criteriaType: null,
      headers: [
        {
          text: '',
          value: 'actions',
          sortable: false,
          width: '5%'
        },
        { text: this.$t('CriteriaTemplateTable.indications'), value: 'indications.name' },
        { text: this.$t('CriteriaTemplateTable.criterion_cat'), value: 'categories' },
        { text: this.$t('CriteriaTemplateTable.criterion_sub_cat'), value: 'subCategories' },
        { text: this.$t('CriteriaTemplateTable.criterion_tpl'), value: 'name', width: '30%' },
        { text: this.$t('CriteriaTemplateTable.guidance_text'), value: 'guidanceText', width: '30%' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' }
      ],
      types: [],
      urlPrefix: '/criteria-templates'
    }
  },
  methods: {
    getExtraFilters (filters) {
      filters['type.termUid'] = { v: [this.criteriaType] }
    },
    prepareIndexingPayload (form) {
      return this.$refs.indexingForm.preparePayload(form)
    },
    refreshTable () {
      this.$refs.table.$refs.sponsorTable.filter()
    }
  },
  created () {
    this.$store.dispatch('studiesGeneral/fetchNullValues')
    terms.getByCodelist('criteriaTypes').then(resp => {
      this.types = resp.data.items
      const type = this.types.find(item => item.sponsorPreferredName.toLowerCase().startsWith(this.type))
      this.criteriaType = type.termUid
      this.$refs.table.$refs.sponsorTable.filter()
    })
  }
}
</script>
