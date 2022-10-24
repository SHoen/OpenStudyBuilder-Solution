<template>
<div>
  <div class="mt-6 d-flex align-center">
    <v-card-title class="text-h6 ml-2">{{ $t('StudyPopulationView.title') }}</v-card-title>
    </div>
    <div>
    <v-radio-group
      v-model="expand"
      row
      class="pt-2 ml-5"
    >
      <v-radio
        :label="$t('StudyPopulationView.show_all')"
        :value="true"
      ></v-radio>
      <v-radio
        :label="$t('StudyPopulationView.hide_all')"
        :value="false"
      ></v-radio>
    </v-radio-group>
  </div>
  <v-expansion-panels
    :key="key"
    multiple
    v-model="panel"
    flat
    tile
    accordion>
    <v-expansion-panel v-for="(criterias, name,) in studyCriterias" :key="name">
      <v-expansion-panel-header
        v-if="criterias.length > 0"
        class="text-h6 grey--text"
        v-html="name"
        >
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <ol>
          <li v-for="(item, index) in criterias" :key="index" v-html="item"></li>
        </ol>
      </v-expansion-panel-content>
    </v-expansion-panel>
  </v-expansion-panels>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import study from '@/api/study'

export default {
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      studyCriterias: {
        'Inclusion Criteria': [], // Hardcoded to keep correct order
        'Exclusion Criteria': [],
        'Run-in Criteria': [],
        'Randomisation Criteria': [],
        'Dosing Criteria': [],
        'Withdrawal Criteria': []
      },
      key: 0,
      panel: [],
      expand: false
    }
  },
  mounted () {
    study.getStudyCriteria(this.selectedStudy.uid).then(resp => {
      resp.data.forEach(el => {
        if (el.criteriaType.sponsorPreferredName in this.studyCriterias) {
          this.studyCriterias[el.criteriaType.sponsorPreferredName].push(el.criteria ? this.removeBrackets(el.criteria.name) : this.removeBrackets(el.criteriaTemplate.name))
        } else {
          this.studyCriterias[el.criteriaType.sponsorPreferredName] = []
          this.studyCriterias[el.criteriaType.sponsorPreferredName].push(el.criteria ? this.removeBrackets(el.criteria.name) : this.removeBrackets(el.criteriaTemplate.name))
        }
      })
      this.key += 1
    })
  },
  methods: {
    openAll () {
      let length = Object.keys(this.studyCriterias).length
      while (length >= 0) {
        this.panel.push(length)
        length--
      }
    },
    closeAll () {
      this.panel = []
    },
    removeBrackets (value) {
      return value.replaceAll('[', '').replaceAll(']', '')
    }
  },
  watch: {
    expand (value) {
      value ? this.openAll() : this.closeAll()
    }
  }
}
</script>
