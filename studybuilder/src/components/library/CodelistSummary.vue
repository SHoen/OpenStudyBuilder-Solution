<template>
<v-expansion-panels
  flat
  tile
  accordion>
  <v-expansion-panel>
    <v-expansion-panel-header data-cy="cl-summary-title" class="text-h6 grey--text">{{ $t('CodelistSummary.title') }}</v-expansion-panel-header>
    <v-expansion-panel-content>
      <v-row class="mt-2 mb-4">
        <v-col cols="9">
          <v-row>
            <v-col sm="2" md="1">
              <span class="v-label">{{ $t('CodelistSummary.concept_id') }}</span>
            </v-col>
            <v-col data-cy="Concept ID"  sm="10" md="11">
              {{ codelistAttributes.codelist_uid }}
            </v-col>
          </v-row>
        </v-col>
      </v-row>
      <v-row class="my-4">
        <v-col cols="9">
          <v-row>
            <v-col sm="2" md="1">
              <span class="v-label">{{ $t('_global.name') }}</span>
            </v-col>
            <v-col data-cy="Name" sm="10" md="11">
              {{ codelistAttributes.name }}
            </v-col>
            <v-col sm="2" md="1">
              <span class="v-label">{{ $t('_global.label') }}</span>
            </v-col>
            <v-col data-cy="Label" sm="10" md="11">
              {{ codelistNames.name }}
            </v-col>
            <v-col sm="2" md="1">
              <span class="v-label">{{ $t('_global.definition') }}</span>
            </v-col>
            <v-col data-cy="Definition" sm="10" md="11">
              {{ codelistAttributes.definition }}
            </v-col>
          </v-row>
        </v-col>
        <v-col cols="3">
          <v-row>
            <v-col cols="6">
              <span class="v-label">{{ $t('_global.library') }}</span>
            </v-col>
            <v-col data-cy="Library" cols="6">
              {{ codelistNames.library_name }}
            </v-col>
            <v-col cols="6">
              <span class="v-label">{{ $t('CtCatalogueTable.template_parameter') }}</span>
            </v-col>
            <v-col data-cy="Template parameter" cols="6">
              {{ codelistNames.template_parameter|yesno }}
            </v-col>
            <v-col cols="6">
              <span class="v-label">{{ $t('CtCatalogueTable.extensible') }}</span>
            </v-col>
            <v-col data-cy="Extensible" cols="6">
              {{ codelistAttributes.extensible|yesno }}
            </v-col>
          </v-row>
        </v-col>
      </v-row>
    </v-expansion-panel-content>
  </v-expansion-panel>
</v-expansion-panels>
</template>

<script>
export default {
  props: ['codelistNames', 'codelistAttributes']
}
</script>

<style scoped>
.col {
  padding-top: 2px !important;
  padding-bottom: 2px !important;
}
</style>
