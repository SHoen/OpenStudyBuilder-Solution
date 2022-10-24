<template>
<studybuilder-template-table
  url-prefix="/timeframe-templates"
  translation-type='TimeframeTemplateTable'
  object-type="timeframeTemplates"
  :with-indexing-properties="false"
  >
  <template v-slot:editform="{ closeForm, selectedObject, filter, updateTemplate }">
    <studybuilder-template-form
      @close="closeForm"
      :template="selectedObject"
      url-prefix="/timeframe-templates"
      translation-type="TimeframeTemplateTable"
      object-type="timeframeTemplates"
      :with-classification-attributes="false"
      @templateAdded="filter()"
      @templateUpdated="updateTemplate(arguments[0], 'Draft')"
      />
  </template>
</studybuilder-template-table>
</template>

<script>
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable'
import StudybuilderTemplateForm from '@/components/library/StudybuilderTemplateForm'

export default StudybuilderTemplateTable.extend({
  name: 'timeframe-template-table',
  components: {
    StudybuilderTemplateForm
  }
})
</script>
