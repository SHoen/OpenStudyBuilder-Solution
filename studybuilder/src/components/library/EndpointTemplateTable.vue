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
  :history-formating-func="formatHistoryItem"
  :history-excluded-headers="historyExcludedHeaders"
  :prepare-duplicate-payload-func="prepareDuplicatePayload"
  :default-filters="defaultFilters"
  >
  <template v-slot:editform="{ closeForm, selectedObject, preInstanceMode }">
    <endpoint-template-pre-instance-form
      v-if="preInstanceMode"
      :pre-instance="selectedObject"
      @close="closeForm"
      @success="refreshTable()"
      />
    <endpoint-template-form
      v-else
      @close="closeForm"
      @templateAdded="refreshTable"
      @templateUpdated="refreshTable"
      :template="selectedObject"
      />
  </template>
  <template v-slot:item.categories.name.sponsor_preferred_name="{ item }">
    <template v-if="item.categories && item.categories.length">
      {{ item.categories|terms }}
    </template>
    <template v-else>
      {{ $t('_global.not_applicable_long') }}
    </template>
  </template>
  <template v-slot:item.sub_categories.name.sponsor_preferred_name="{ item }">
    <template v-if="item.sub_categories && item.sub_categories.length">
      {{ item.sub_categories|terms }}
    </template>
    <template v-else>
      {{ $t('_global.not_applicable_long') }}
    </template>
  </template>
  <template v-slot:indexingDialog="{ closeDialog, template, show, preInstanceMode }">
    <template-indexing-dialog
      @close="closeDialog"
      @updated="refreshTable"
      :show="show"
      :template="template"
      :prepare-payload-func="prepareIndexingPayload"
      :url-prefix="urlPrefix"
      :pre-instance-mode="preInstanceMode"
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
  <template v-slot:preInstanceForm="{ closeDialog, template }">
    <endpoint-template-pre-instance-form
      :template="template"
      @close="closeDialog"
      @success="refreshTable"
      />
  </template>
</studybuilder-template-table>
</template>

<script>
import dataFormating from '@/utils/dataFormating'
import EndpointTemplateForm from '@/components/library/EndpointTemplateForm'
import EndpointTemplateIndexingForm from './EndpointTemplateIndexingForm'
import EndpointTemplatePreInstanceForm from './EndpointTemplatePreInstanceForm'
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable'
import TemplateIndexingDialog from './TemplateIndexingDialog'

export default {
  components: {
    EndpointTemplateForm,
    EndpointTemplateIndexingForm,
    EndpointTemplatePreInstanceForm,
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
        { text: this.$t('_global.sequence_number'), value: 'sequence_id' },
        { text: this.$t('_global.parent_template'), value: 'name', width: '30%', filteringName: 'name_plain' },
        { text: this.$t('_global.modified'), value: 'start_date' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' }
      ],
      defaultFilters: [
        { text: this.$t('_global.indications'), value: 'indications.name' },
        { text: this.$t('EndpointTemplateTable.endpoint_cat'), value: 'categories.name.sponsor_preferred_name' },
        { text: this.$t('EndpointTemplateTable.endpoint_sub_cat'), value: 'sub_categories.name.sponsor_preferred_name' }
      ],
      historyExcludedHeaders: [
        'indications.name',
        'categories.name.sponsor_preferred_name',
        'sub_categories.name.sponsor_preferred_name'
      ],
      urlPrefix: '/endpoint-templates'
    }
  },
  methods: {
    prepareIndexingPayload (form) {
      return this.$refs.indexingForm.preparePayload(form)
    },
    prepareDuplicatePayload (payload, preInstance) {
      if (preInstance.categories && preInstance.categories.length) {
        payload.category_uids = preInstance.categories.map(item => item.term_uid)
      } else {
        payload.category_uids = []
      }
      if (preInstance.sub_categories && preInstance.sub_categories.length) {
        payload.sub_category_uids = preInstance.sub_categories.map(item => item.term_uid)
      } else {
        payload.sub_category_uids = []
      }
    },
    refreshTable () {
      this.$refs.table.$refs.sponsorTable.filter()
      if (this.$refs.table.$refs.preInstanceTable) {
        this.$refs.table.$refs.preInstanceTable.filter()
      }
    },
    formatHistoryItem (item) {
      if (item.categories) {
        item.categories = { name: { sponsor_preferred_name: dataFormating.terms(item.categories) } }
      } else {
        item.categories = { name: { sponsor_preferred_name: this.$t('_global.not_applicable_long') } }
      }
      if (item.sub_categories) {
        item.sub_categories = { name: { sponsor_preferred_name: dataFormating.terms(item.sub_categories) } }
      } else {
        item.sub_categories = { name: { sponsor_preferred_name: this.$t('_global.not_applicable_long') } }
      }
    }
  }
}
</script>
