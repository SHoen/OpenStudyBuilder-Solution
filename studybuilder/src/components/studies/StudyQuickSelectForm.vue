<template>
<v-card data-cy="form-body" color="white">
  <v-card-title>
    <span class="dialog-title">{{ $t('StudyQuickSelectForm.title') }}</span>
  </v-card-title>
  <v-card-text>
    <validation-observer ref="observer">
      <v-row class="mt-4">
        <v-col cols="6">
          <validation-provider
            v-slot="{ errors }"
            rules="atleastone:@studyId"
            vid="studyId"
            >
            <v-autocomplete
              v-model="studyById"
              :label="$t('StudyQuickSelectForm.study_id')"
              :items="studiesWithId"
              item-text="studyId"
              return-object
              :error-messages="errors"
              clearable
              @change="autoPopulateAcronym"
              />
          </validation-provider>
        </v-col>
        <v-col cols="6">
          <validation-provider
            v-slot="{ errors }"
            rules="atleastone:@studyAcronym"
            vid="studyAcronym"
            >
            <v-autocomplete
              v-model="studyByAcronym"
              :label="$t('StudyQuickSelectForm.study_acronym')"
              :items="studiesWithAcronym"
              item-text="studyAcronym"
              return-object
              :error-messages="errors"
              clearable
              @change="autoPopulateId"
              />
          </validation-provider>
        </v-col>
      </v-row>
    </validation-observer>
  </v-card-text>
  <v-spacer v-if="expand || expand2" class="distance"></v-spacer>
  <v-card-actions class="pb-4">
    <v-spacer />
    <v-btn
      class="secondary-btn"
      color="white"
      elevation="3"
      @click="close"
      >
      {{ $t('_global.cancel') }}
    </v-btn>
    <v-btn
      color="secondary"
      elevation="3"
      @click="select"
      >
      {{ $t('_global.ok') }}
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
import study from '@/api/study'

export default {
  computed: {
    studiesWithId () {
      return this.studies.filter(study => study.studyId !== null)
    },
    studiesWithAcronym () {
      return this.studies.filter(study => study.studyAcronym !== null)
    }
  },
  data () {
    return {
      studyById: null,
      studyByAcronym: null,
      studies: [],
      expand: false,
      expand2: false
    }
  },
  methods: {
    close () {
      this.$emit('close')
    },
    async select () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      if (this.studyById) {
        this.$store.commit('studiesGeneral/SELECT_STUDY', this.studyById)
      } else {
        this.$store.commit('studiesGeneral/SELECT_STUDY', this.studyByAcronym)
      }
      this.$emit('selected')
      this.close()
    },
    autoPopulateAcronym (study) {
      if (study && study.studyAcronym) {
        this.studyByAcronym = study
      }
    },
    autoPopulateId (study) {
      if (study && study.studyId) {
        this.studyById = study
      }
    }
  },
  mounted () {
    study.getAll().then(resp => {
      this.studies = resp.data.items
    })
  }
}
</script>

<style scoped>
.distance {
  margin-bottom: 260px;
}
</style>
