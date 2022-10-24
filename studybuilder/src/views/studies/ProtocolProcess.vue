<template>
<div class="px-4">
  <div class="page-title">{{ $t('ProtocolProcessView.title') }}</div>
  <v-card flat>
    <v-card-title class="text-h6">{{ $t('ProtocolProcessView.sub_title') }}</v-card-title>
    <v-card-text>
      <p>{{ $t('ProtocolProcessView.description') }}</p>
      <div class="d-flex flex-wrap align-center">
        <div v-for="(step, index) in protocol" :key="index" class="d-flex mt-4 text-center align-center">
          <v-menu offset-y v-if="step.items">
            <template v-slot:activator="{ on, attrs }">
              <v-btn
                color="primary"
                :class="step.padding ? step.padding : 'pa-6'"
                style="max-width: 150px"
                :data-cy=step.title
                v-bind="attrs"
                v-on="on"
                >
                {{ step.title }}
              </v-btn>
            </template>
            <v-list>
              <v-list-item
                v-for="(item, index) in step.items"
                :key="index"
                @click="navigate(item.to)"
                >
                <v-list-item-title>{{ item.title }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          <v-btn
            v-else-if="step.click"
            color="primary"
            :class="step.padding ? step.padding : 'pa-6'"
            style="max-width: 150px"
            :data-cy=step.title
            @click="step.click"
            >
            {{ step.title }}
          </v-btn>
          <v-btn
            v-else
            color="primary"
            :class="step.padding ? step.padding : 'pa-6'"
            style="max-width: 150px"
            :data-cy=step.title
            @click="navigate(step.to)"
            >
            {{ step.title }}
          </v-btn>
          <v-icon large v-if="index !== protocol.length - 1 && !step.separatorText" class="mx-4" color="secondary">
            mdi-arrow-right-bold
          </v-icon>
          <span v-if="index !== protocol.length - 1 && step.separatorText" class="mx-6 secondary--text"><strong>{{ step.separatorText }}</strong></span>
        </div>
      </div>
    </v-card-text>
  </v-card>
  <confirm-dialog ref="confirm" :text-cols="5" :action-cols="6">
    <template v-slot:actions>
      <v-btn
        color="white"
        :data-cy=step.title
        @click.native="openSelectStudyDialog"
        outlined
        class="mr-2"
        elevation="2"
        >
        {{ $t('_global.select_study') }}
      </v-btn>
      <v-btn
        color="white"
        :data-cy=step.title
        @click.native="redirectToStudyTable"
        outlined
        elevation="2"
        >
        {{ $t('_global.add_study') }}
      </v-btn>
    </template>
  </confirm-dialog>
  <v-dialog
    v-model="showSelectForm"
    persistent
    max-width="600px"
    >
    <study-quick-select-form @close="showSelectForm = false" @selected="goToNextUrl" />
  </v-dialog>
</div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import StudyQuickSelectForm from '@/components/studies/StudyQuickSelectForm'

export default {
  components: {
    ConfirmDialog,
    StudyQuickSelectForm
  },
  computed: {
    ...mapGetters({
      findMenuItemPath: 'app/findMenuItemPath',
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      protocol: [
        {
          title: this.$t('ProtocolProcessView.select_study'),
          click: this.showForm,
          separatorText: 'OR'
        },
        {
          title: this.$t('ProtocolProcessView.add_new_study'),
          to: { name: 'SelectOrAddStudy' }
        },
        {
          title: this.$t('ProtocolProcessView.study_design'),
          items: [
            {
              title: this.$t('ProtocolProcessView.study_type'),
              to: { name: 'StudyDesign', params: { tab: 'type' } }
            },
            {
              title: this.$t('ProtocolProcessView.study_arms'),
              to: { name: 'StudyDesign', params: { tab: 'arms' } }
            },
            {
              title: this.$t('ProtocolProcessView.study_epochs'),
              to: { name: 'StudyDesign', params: { tab: 'epochs' } }
            },
            {
              title: this.$t('ProtocolProcessView.study_elements'),
              to: { name: 'StudyDesign', params: { tab: 'elements' } }
            },
            {
              title: this.$t('ProtocolProcessView.study_visits'),
              to: { name: 'StudyDesign', params: { tab: 'visits' } }
            },
            {
              title: this.$t('ProtocolProcessView.design_matrix'),
              to: { name: 'StudyDesign', params: { tab: 'design_matrix' } }
            }
          ]
        },
        {
          title: this.$t('ProtocolProcessView.study_purpose'),
          items: [
            {
              title: this.$t('ProtocolProcessView.study_title'),
              to: { name: 'StudyTitle' }
            },
            {
              title: this.$t('ProtocolProcessView.objectives'),
              to: { name: 'StudyPurpose', params: { tab: 'objectives' } }
            },
            {
              title: this.$t('ProtocolProcessView.endpoints'),
              to: { name: 'StudyPurpose', params: { tab: 'endpoints' } }
            }
          ]
        },
        {
          title: this.$t('ProtocolProcessView.study_population'),
          items: [
            {
              title: this.$t('ProtocolProcessView.study_population'),
              to: { name: 'StudyPopulation' }
            },
            {
              title: this.$t('ProtocolProcessView.inclusion_criteria'),
              to: { name: 'StudySelectionCriteria', params: { tab: 'Inclusion Criteria' } }
            },
            {
              title: this.$t('ProtocolProcessView.exclusion_criteria'),
              to: { name: 'StudySelectionCriteria', params: { tab: 'Exclusion Criteria' } }
            },
            {
              title: this.$t('ProtocolProcessView.runin_criteria'),
              to: { name: 'StudySelectionCriteria', params: { tab: 'Run-in Criteria' } }
            },
            {
              title: this.$t('ProtocolProcessView.randomisation_criteria'),
              to: { name: 'StudySelectionCriteria', params: { tab: 'Randomisation Criteria' } }
            },
            {
              title: this.$t('ProtocolProcessView.dosing_criteria'),
              to: { name: 'StudySelectionCriteria', params: { tab: 'Dosing Criteria' } }
            },
            {
              title: this.$t('ProtocolProcessView.withdrawal_criteria'),
              to: { name: 'StudySelectionCriteria', params: { tab: 'Withdrawal Criteria' } }
            }
          ]
        },
        {
          title: this.$t('ProtocolProcessView.study_interventions'),
          items: [
            {
              title: this.$t('ProtocolProcessView.intervention_type'),
              to: { name: 'StudyInterventions', params: { tab: 'intervention_type' } }
            },
            {
              title: this.$t('ProtocolProcessView.study_compounds'),
              to: { name: 'StudyInterventions', params: { tab: 'study_compounds' } }
            },
            {
              title: this.$t('ProtocolProcessView.other_interventions'),
              to: { name: 'StudyInterventions', params: { tab: 'other_interventions' } }
            }
          ]
        },
        {
          title: this.$t('ProtocolProcessView.schedules'),
          items: [
            {
              title: this.$t('ProtocolProcessView.activity_list'),
              to: { name: 'StudyActivities', params: { tab: 'list' } }
            },
            {
              title: this.$t('ProtocolProcessView.detailed_flowchart'),
              to: { name: 'StudyActivities', params: { tab: 'detailed' } }
            },
            {
              title: this.$t('ProtocolProcessView.protocol_flowchart'),
              to: { name: 'StudyActivities', params: { tab: 'protocol' } }
            },
            {
              title: this.$t('ProtocolProcessView.activity_instructions'),
              to: { name: 'StudyActivities', params: { tab: 'instructions' } }
            }
          ]
        }
      ],
      showSelectForm: false
    }
  },
  methods: {
    ...mapActions({
      addBreadcrumbsLevel: 'app/addBreadcrumbsLevel'
    }),
    async navigate (to) {
      this.nextUrl = to
      if (to.name !== 'SelectOrAddStudy' && !this.selectedStudy) {
        const options = {
          type: 'warning'
        }
        await this.$refs.confirm.open(this.$t('_global.no_study_selected'), options)
        return
      }
      this.goToNextUrl()
    },
    showForm () {
      this.showSelectForm = true
    },
    goToNextUrl () {
      const [menuItem, menuSubItem] = this.findMenuItemPath('Studies', this.nextUrl.name)
      this.$store.commit('app/SET_SECTION', 'Studies')
      this.$router.push(this.nextUrl)
      this.nextUrl = null
      if (menuItem) {
        this.addBreadcrumbsLevel({ text: menuItem.title, to: menuItem.url, index: 1 })
        if (menuSubItem) {
          this.addBreadcrumbsLevel({ text: menuSubItem.title, to: menuSubItem.url })
        }
      }
    },
    openSelectStudyDialog () {
      this.$refs.confirm.cancel()
      this.showSelectForm = true
    },
    redirectToStudyTable () {
      this.$refs.confirm.cancel()
      this.$router.push({ name: 'SelectOrAddStudy' })
    }
  }
}
</script>

<style lang="scss">
.v-btn {
  &__content {
    width: 100% !important;
    white-space: normal !important;
  }
}
</style>
