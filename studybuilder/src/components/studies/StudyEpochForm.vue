<template>
<simple-form-dialog
  ref="form"
  :title="title"
  :help-items="helpItems"
  :help-text="$t('_help.StudyDefineForm.general')"
  @close="cancel"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <v-alert
      v-if="studyEpoch && studyEpoch.studyVisitCount > 0"
      type="warning"
      >
      {{ $t('StudyEpochForm.epoch_linked_to_visits_warning', { epoch: studyEpoch.epochName }) }}
    </v-alert>
    <validation-observer ref="observer">
      <v-row>
        <v-col cols="6">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-autocomplete
              :label="$t('StudyEpochForm.epoch_type')"
              :items="typeGroups"
              item-text="type_name"
              item-value="type"
              dense
              :error-messages="errors"
              clearable
              data-cy="epoch-type"
              v-model="form.epochType"
              @input="setEpochGroups()"
              @click:clear="setEpochGroups()"
              :disabled="studyEpoch && studyEpoch.studyVisitCount > 0"
              />
          </validation-provider>
        </v-col>
        <v-col cols="6">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-autocomplete
              :label="$t('StudyEpochForm.epoch_subtype')"
              :items="subtypeGroups"
              item-text="subtype_name"
              item-value="subtype"
              dense
              :error-messages="errors"
              clearable
              data-cy="epoch-subtype"
              v-model="form.epochSubType"
              @input="setEpochGroups()"
              @click:clear="setEpochGroups()"
              :disabled="studyEpoch && studyEpoch.studyVisitCount > 0"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row>
          <v-col>
            <v-text-field
              data-cy="select-epoch"
              :label="$t('StudyEpochForm.name')"
              dense
              disabled
              v-model="epochDisplay"
              filled
              :error-messages="errors"
              :key="typeTrigger"
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row>
          <v-col>
            <v-textarea
              data-cy="epoch-start-rule"
              id="startRule"
              :label="$t('StudyEpochForm.start_rule')"
              v-model="form.startRule"
              rows="1"
              auto-grow
              :error-messages="errors"
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row>
          <v-col>
            <v-textarea
              data-cy="epoch-end-rule"
              id="endRule"
              :label="$t('StudyEpochForm.stop_rule')"
              v-model="form.endRule"
              rows="1"
              auto-grow
              :error-messages="errors"
              />
          </v-col>
        </v-row>
      </validation-provider>
      <v-row>
        <v-col>
          <v-textarea
            id="description"
            data-cy="description"
            :label="$t('StudyEpochForm.description')"
            v-model="form.description"
            rows="1"
            auto-grow
            />
        </v-col>
      </v-row>
      <validation-provider
        v-if="studyEpoch"
        v-slot="{ errors }"
        rules="required"
        >
        <label class="v-label">{{ $t('_global.change_description') }}</label>
        <v-textarea
          v-model="form.changeDescription"
          :error-messages="errors"
          dense
          clearable
          rows="1"
          auto-grow
          />
      </validation-provider>
      <div class="mt-4">
        <label class="v-label">{{ $t('StudyEpochForm.color') }}</label>
        <v-color-picker
          data-cy="epoch-color-picker"
          v-model="colorHash"
          clearable
          show-swatches
          hide-canvas
          hide-sliders
          swatches-max-height="300px"
          />
      </div>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>
import _isEmpty from 'lodash/isEmpty'
import _isEqual from 'lodash/isEqual'
import { mapGetters } from 'vuex'
import units from '@/api/units'
import { bus } from '@/main'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import studyEpochs from '../../api/studyEpochs'

export default {
  components: {
    SimpleFormDialog
  },
  props: {
    studyEpoch: Object,
    open: Boolean
  },
  computed: {
    title () {
      return (this.studyEpoch) ? this.$t('StudyEpochForm.edit_title') : this.$t('StudyEpochForm.add_title')
    },
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyEpochs: 'studyEpochs/studyEpochs',
      groups: 'studyEpochs/allowedConfigs'
    })
  },
  data () {
    return {
      colorHash: null,
      epochs: [],
      form: {},
      helpItems: [
        'StudyEpochForm.name',
        'StudyEpochForm.epoch_type',
        'StudyEpochForm.epoch_subtype',
        'StudyEpochForm.description',
        'StudyEpochForm.start_rule',
        'StudyEpochForm.stop_rule',
        'StudyEpochForm.epoch_time_unit',
        'StudyEpochForm.expected_epoch_duration',
        'StudyEpochForm.color'
      ],
      timeUnits: [],
      typeTrigger: 0,
      typeGroups: [],
      subtypeGroups: [],
      epochDisplay: ''
    }
  },
  methods: {
    createMapping (codelist) {
      const returnValue = {}
      codelist.forEach(item => {
        returnValue[item.termUid] = item.sponsorPreferredName
      })
      return returnValue
    },
    close () {
      this.$emit('close')
      this.form = {}
      this.colorHash = null
      this.$refs.observer.reset()
      this.typeGroups = this.groups
      this.subtypeGroups = this.groups
    },
    async cancel () {
      if ((!this.studyEpoch && !_isEmpty(this.form)) || (this.studyEpoch && !_isEqual(this.form, this.studyEpoch))) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue')
        }
        if (await this.$refs.form.confirm(this.$t('_global.cancel_changes'), options)) {
          this.close()
        }
      } else {
        this.close()
      }
    },
    setEpochGroups () {
      let type = ''
      let subtype = ''
      if (!this.form.epochSubType && !this.form.epochType) {
        this.$set(this.form, 'epoch', '')
        this.subtypeGroups = this.groups
        this.typeGroups = this.groups
        this.epochDisplay = ''
      } else if (!this.form.epochSubType) {
        this.$set(this.form, 'epoch', '')
        type = this.form.epochType
        this.subtypeGroups = this.groups
        this.typeGroups = this.groups
        this.subtypeGroups = this.groups.filter(function (value) {
          return value.type === type
        })
        this.epochDisplay = ''
      } else if (!this.form.epochType) {
        this.$set(this.form, 'epoch', '')
        subtype = this.form.epochSubType
        this.typeGroups = this.groups
        this.subtypeGroups = this.groups
        this.typeGroups = this.groups.filter(function (value) {
          return value.subtype === subtype
        })
        this.epochDisplay = ''
      } else {
        subtype = this.form.epochSubType
        type = this.form.epochType
        this.typeGroups = this.groups.filter(function (value) {
          return value.subtype === subtype
        })
        this.subtypeGroups = this.groups.filter(function (value) {
          return value.type === type
        })

        const data = {
          studyUid: this.selectedStudy.uid,
          epochSubType: subtype
        }
        studyEpochs.getPreviewEpoch(this.selectedStudy.uid, data).then(resp => {
          this.$set(this.form, 'epoch', resp.data.epoch)
          this.epochDisplay = resp.data.epochName
        })
      }
    },
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.$refs.form.working = true
      try {
        if (!this.studyEpoch) {
          await this.addObject()
        } else {
          await this.updateObject()
        }
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    },
    addObject () {
      const data = JSON.parse(JSON.stringify(this.form))
      if (this.colorHash) {
        data.colorHash = this.colorHash.hexa
      }
      data.studyUid = this.selectedStudy.uid
      return this.$store.dispatch('studyEpochs/addStudyEpoch', { studyUid: this.selectedStudy.uid, input: data }).then(resp => {
        this.$store.dispatch('studyEpochs/fetchStudyEpochs', this.selectedStudy.uid)
        bus.$emit('notification', { msg: this.$t('StudyEpochForm.add_success') })
      })
    },
    updateObject () {
      const data = JSON.parse(JSON.stringify(this.form))
      if (this.colorHash) {
        data.colorHash = this.colorHash.hexa !== undefined ? this.colorHash.hexa : this.colorHash
      }
      return this.$store.dispatch('studyEpochs/updateStudyEpoch', { studyUid: this.selectedStudy.uid, studyEpochUid: this.studyEpoch.uid, input: data }).then(resp => {
        this.$store.dispatch('studyEpochs/fetchStudyEpochs', this.selectedStudy.uid)
        bus.$emit('notification', { msg: this.$t('StudyEpochForm.update_success') })
      })
    },
    loadFromStudyEpoch (studyEpoch) {
      this.form = { ...studyEpoch }
      if (studyEpoch.colorHash) {
        this.colorHash = studyEpoch.colorHash
      }
    }
  },
  mounted () {
    this.$store.dispatch('studyEpochs/fetchAllowedConfigs')
    units.getByDimension('TIME').then(resp => {
      this.timeUnits = resp.data.items
    })
    if (this.studyEpoch) {
      this.loadFromStudyEpoch(this.studyEpoch)
      this.setEpochGroups()
    }
  },
  watch: {
    studyEpoch (value) {
      if (value) {
        this.loadFromStudyEpoch(value)
      }
    },
    groups () {
      this.typeGroups = this.groups
      this.subtypeGroups = this.groups
    }
  }
}
</script>
<style>
.v-color-picker__controls {
  display: none
}
</style>
