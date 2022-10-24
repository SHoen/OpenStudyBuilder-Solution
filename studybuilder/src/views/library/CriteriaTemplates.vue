<template>
<div class="px-4">
  <div class="page-title d-flex align-center">
    {{ $t('CriteriaTemplatesView.title') }}
    <help-button :help-text="$t('_help.CriteriaTemplatesTable.general')" />
  </div>
  <v-tabs v-model="tab">
    <v-tab v-for="category in categories" :key="category.value">
      {{ category.text }}
    </v-tab>
  </v-tabs>
  <v-tabs-items v-model="tab">
    <v-tab-item v-for="category in categories" :key="category.value">
      <criteria-template-table
        :key="category.value"
        :type="category.value"
        :criterion-categories="category.criterionCategories"
        />
    </v-tab-item>
  </v-tabs-items>
</div>
</template>

<script>
import CriteriaTemplateTable from '@/components/library/CriteriaTemplateTable'
import HelpButton from '@/components/tools/HelpButton'

export default {
  components: {
    CriteriaTemplateTable,
    HelpButton
  },
  data () {
    return {
      categories: [
        {
          text: this.$t('CriteriaTemplatesView.inclusion_criteria'),
          value: 'inclusion',
          criterionCategories: [
            'Body mass index',
            'Diabetes history or HbA1c related criteria',
            'General health status',
            'Lifestyle',
            'Meal habits',
            'Medication',
            'Race or nationality',
            'Weight loss history'
          ]
        },
        {
          text: this.$t('CriteriaTemplatesView.exclusion_criteria'),
          value: 'exclusion',
          criterionCategories: [
            'Alcohol, tobacco, and drugs of abuse',
            'Blood donation',
            'Cardiovascular disease',
            'Diabetes history or HbA1c related criteria',
            'Diabetic retinopathy',
            'ECG activity',
            'Gastrointestinal disorders',
            'Gastrointestinal surgery',
            'GCP',
            'General health status',
            'Glucose metabolism',
            'HIV and hepatitis',
            'Hypoglycaemia',
            'Ketoacidosis',
            'Major surgery',
            'Meal habits',
            'General medical history',
            'Medication',
            'MEN2 or MTC',
            'Mental health',
            'Neoplasm',
            'Pancreatitis',
            'Renal function',
            'Safety laboratory parameters',
            'Thromboembolic disease',
            'Thyroid disease',
            'Vital signs',
            'Vulnerable subjects',
            'Weight loss history',
            'Weight-loss surgery'
          ]
        },
        {
          text: this.$t('CriteriaTemplatesView.runin_criteria'),
          value: 'run-in',
          criterionCategories: []
        },
        {
          text: this.$t('CriteriaTemplatesView.randomisation_criteria'),
          value: 'randomisation',
          criterionCategories: []
        },
        {
          text: this.$t('CriteriaTemplatesView.dosing_criteria'),
          value: 'dosing',
          criterionCategories: []
        },
        {
          text: this.$t('CriteriaTemplatesView.withdrawal_criteria'),
          value: 'withdrawal',
          criterionCategories: []
        }
      ],
      tab: null
    }
  }
}
</script>
