<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('Sidebar.study.study_structure') }} ({{ studyId }})
    <help-button-with-panels
      :help-text="$t('_help.StudyStructure.general')"
      :items="helpItems"
      />

  </div>
  <v-tabs v-model="tab">
    <v-tab href="#arms">{{ $t('Sidebar.study.study_arms') }}</v-tab>
    <v-tab href="#branches">{{ $t('Sidebar.study.study_branches') }}</v-tab>
    <v-tab href="#cohorts">{{ $t('Sidebar.study.study_cohorts') }}</v-tab>
    <v-tab href="#epochs">{{ $t('Sidebar.study.study_epochs') }}</v-tab>
    <v-tab href="#elements">{{ $t('Sidebar.study.study_elements') }}</v-tab>
    <v-tab href="#visits">{{ $t('Sidebar.study.study_visits') }}</v-tab>
    <v-tab href="#design_matrix" @click="refreshMatrix()">{{ $t('Sidebar.study.design_matrix') }}</v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item id="arms">
      <study-arms-table />
    </v-tab-item>
    <v-tab-item id="branches">
      <study-branches-table />
    </v-tab-item>
    <v-tab-item id="cohorts">
      <study-cohorts-table />
    </v-tab-item>
    <v-tab-item id="elements">
      <study-elements-table />
    </v-tab-item>
    <v-tab-item id="epochs">
      <study-epoch-table />
    </v-tab-item>
    <v-tab-item id="visits">
      <study-visit-table />
    </v-tab-item>
    <v-tab-item id="design_matrix">
      <design-matrix-table :refresh="key"/>
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import DesignMatrixTable from '@/components/studies/DesignMatrixTable'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'
import { studySelectedNavigationGuard } from '@/mixins/studies'
import StudyEpochTable from '@/components/studies/StudyEpochTable'
import StudyArmsTable from '@/components/studies/StudyArmsTable'
import StudyBranchesTable from '@/components/studies/StudyBranchesTable'
import StudyVisitTable from '@/components/studies/StudyVisitTable'
import StudyElementsTable from '@/components/studies/StudyElementsTable'
import StudyCohortsTable from '@/components/studies/StudyCohortsTable'

export default {
  mixins: [studySelectedNavigationGuard],
  components: {
    HelpButtonWithPanels,
    StudyVisitTable,
    StudyEpochTable,
    StudyArmsTable,
    DesignMatrixTable,
    StudyElementsTable,
    StudyBranchesTable,
    StudyCohortsTable
  },
  data () {
    return {
      helpItems: [
        'StudyStructure.study_arms',
        'StudyStructure.study_branches',
        'StudyStructure.study_cohorts',
        'StudyStructure.study_epochs',
        'StudyStructure.study_elements',
        'StudyStructure.study_visits',
        'StudyStructure.design_matrix',
        'StudyStructure.edit_visit_tableview'
      ],
      key: 0,
      tab: null
    }
  },
  mounted () {
    this.tab = this.$route.params.tab
  },
  methods: {
    refreshMatrix () {
      this.key += 1
    }
  },
  watch: {
    tab (newValue) {
      this.$router.push({
        name: 'StudyStructure',
        params: { tab: newValue }
      })
    }
  }
}
</script>
