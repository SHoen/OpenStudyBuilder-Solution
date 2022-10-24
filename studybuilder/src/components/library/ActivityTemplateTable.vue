<template>
<studybuilder-template-table
  ref="table"
  :url-prefix="urlPrefix"
  translation-type="ActivityTemplateTable"
  object-type="activityTemplates"
  :headers="headers"
  fullscreen-form
  >
  <template v-slot:editform="{ closeForm, selectedObject, filter, updateTemplate }">
    <activity-template-form
      @close="closeForm"
      @templateAdded="filter()"
      @templateUpdated="updateTemplate(arguments[0], 'Draft')"
      :template="selectedObject"
      />
  </template>
  <template v-slot:item.activityGroups="{ item }">
    <template v-if="item.activityGroups">
      {{ displayList(item.activityGroups) }}
    </template>
  </template>
  <template v-slot:item.activitySubGroups="{ item }">
    <template v-if="item.activitySubGroups">
      {{ displayList(item.activitySubGroups) }}
    </template>
  </template>
  <template v-slot:item.activities="{ item }">
    <template v-if="item.activities">
      {{ displayList(item.activities) }}
    </template>
    <template v-else-if="item.defaultParameterValuesSet === undefined">
      {{ $t('_global.not_applicable_long') }}
    </template>
  </template>
  <template v-slot:indexingDialog="{ closeDialog, template, show }">
    <template-indexing-dialog
      @close="closeDialog"
      @updated="refreshTable"
      :template="template"
      :prepare-payload-func="prepareIndexingPayload"
      :url-prefix="urlPrefix"
      :open="show"
      >
      <template v-slot:form="{ form }">
        <activity-template-indexing-form
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
import ActivityTemplateForm from './ActivityTemplateForm'
import ActivityTemplateIndexingForm from './ActivityTemplateIndexingForm'
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable'
import TemplateIndexingDialog from './TemplateIndexingDialog'

export default {
  components: {
    ActivityTemplateForm,
    ActivityTemplateIndexingForm,
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
        { text: this.$t('ActivityTemplateTable.indications'), value: 'indications.name' },
        { text: this.$t('ActivityTemplateTable.activity_group'), value: 'activityGroups' },
        { text: this.$t('ActivityTemplateTable.activity_subgroup'), value: 'activitySubGroups' },
        { text: this.$t('ActivityTemplateTable.activity_name'), value: 'activities' },
        { text: this.$t('ActivityTemplateTable.activity_template'), value: 'name', width: '30%' },
        { text: this.$t('_global.modified'), value: 'startDate' },
        { text: this.$t('_global.status'), value: 'status' },
        { text: this.$t('_global.version'), value: 'version' }
      ],
      test: true,
      urlPrefix: '/activity-description-templates'
    }
  },
  methods: {
    displayList (items) {
      return items.map(item => item.name).join(', ')
    },
    prepareIndexingPayload (form) {
      return this.$refs.indexingForm.preparePayload(form)
    },
    refreshTable () {
      this.$refs.table.$refs.sponsorTable.filter()
    }
  },
  mounted () {
    this.$store.dispatch('studiesGeneral/fetchNullValues')
  }
}
</script>
