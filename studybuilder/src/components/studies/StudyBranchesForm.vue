<template>
<simple-form-dialog
  ref="form"
  :title="title"
  :help-items="helpItems"
  @close="cancel"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <validation-provider
        v-slot="{ errors }"
        rules="required"
        >
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.armUid"
              :label="$t('StudyBranchArms.study_arm')"
              data-cy="study-arm"
              :items="arms"
              item-text="name"
              item-value="armUid"
              :error-messages="errors"
              clearable
              :disabled="Object.keys(editedBranchArm).length !== 0"
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules="required|max:200"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('StudyBranchArms.branch_arm_name')"
              data-cy="study-branch-arm-name"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules="required|max:20"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.shortName"
              :label="$t('StudyBranchArms.branch_arm_short_name')"
              data-cy="study-branch-arm-short-name"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules="max:20"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.randomizationGroup"
              :label="$t('StudyBranchArms.randomisation_group')"
              data-cy="study-branch-arm-randomisation-group"
              :error-messages="errors"
              clearable
              @blur="enableBranchCode"
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.code"
              :label="$t('StudyBranchArms.code')"
              data-cy="study-branch-arm-code"
              :rules="codeRules"
              :error-messages="errors"
              clearable
              :disabled="!branchCodeEnable && !isEdit()"
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        :rules="`min_value:1|max_value:${findMaxNuberOfSubjects()}`"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              :disabled="!form.armUid"
              v-model="form.numberOfSubjects"
              :label="$t('StudyBranchArms.nuber_of_subjects')"
              data-cy="study-branch-arm-planned-number-of-subjects"
              :error-messages="(errors[0] && errors[0].includes($t('StudyBranchArms.value_less_then'))) ? $t('StudyBranchArms.number_of_subjects_exceeds') : errors"
              type="number"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.description"
              :label="$t('_global.description')"
              data-cy="study-branch-arm-description"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <div class="mt-4">
        <label class="v-label">{{ $t('StudyBranchArms.colour') }}</label>
        <v-color-picker
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

import { mapGetters } from 'vuex'
import arms from '@/api/arms'
import { bus } from '@/main'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import _isEqual from 'lodash/isEqual'

export default {
  components: {
    SimpleFormDialog
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    title () {
      return (Object.keys(this.editedBranchArm).length !== 0)
        ? this.$t('StudyBranchArms.edit_branch')
        : this.$t('StudyBranchArms.add_branch')
    }
  },
  props: {
    editedBranchArm: Object,
    arms: Array,
    open: Boolean
  },
  data () {
    return {
      form: {},
      helpItems: [],
      editMode: false,
      colorHash: null,
      selectedArm: {},
      branchCodeEnable: false,
      codeRules: []
    }
  },
  methods: {
    enableBranchCode () {
      if (!this.branchCodeEnable) {
        this.$set(this.form, 'code', this.form.randomizationGroup)
        this.branchCodeEnable = true
        this.codeRules = [
          v => (v && v.length <= 20) || this.$t('_errors.max_length_reached', { length: '20' })
        ]
      }
    },
    isEdit () {
      return Object.keys(this.editedBranchArm).length !== 0
    },
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      if (Object.keys(this.editedBranchArm).length !== 0) {
        this.edit()
      } else {
        this.create()
      }
    },
    async create () {
      if (this.colorHash) {
        this.form.colourCode = this.colorHash.hexa
      }
      let armNumberOfSubjects = 0;
      (await arms.getAllBranchesForArm(this.selectedStudy.uid, this.form.armUid)).data.forEach(el => { armNumberOfSubjects += el.numberOfSubjects })
      if (this.selectedArm.numberOfSubjects < (parseInt(armNumberOfSubjects, 10) + parseInt(this.form.numberOfSubjects, 10))) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.save_anyway')
        }
        if (await this.$refs.form.confirm(this.$t('StudyBranchArms.subjects_exceeded'), options)) {
          arms.createBranchArm(this.selectedStudy.uid, this.form).then(resp => {
            bus.$emit('notification', { msg: this.$t('StudyBranchArms.branch_created') })
            this.close()
          })
        }
      } else {
        arms.createBranchArm(this.selectedStudy.uid, this.form).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyBranchArms.branch_created') })
          this.close()
        })
      }
    },
    async edit () {
      if (this.colorHash) {
        this.form.colourCode = this.colorHash.hexa !== undefined ? this.colorHash.hexa : this.colorHash
      }
      let armNumberOfSubjects = 0;
      (await arms.getAllBranchesForArm(this.selectedStudy.uid, this.form.armUid)).data.forEach(el => { armNumberOfSubjects += ((el.branchArmUid === this.editedBranchArm.branchArmUid) ? 0 : el.numberOfSubjects) })
      if (this.selectedArm.numberOfSubjects < (parseInt(armNumberOfSubjects, 10) + parseInt(this.form.numberOfSubjects, 10))) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.save_anyway')
        }
        if (await this.$refs.form.confirm(this.$t('StudyBranchArms.subjects_exceeded'), options)) {
          arms.editBranchArm(this.selectedStudy.uid, this.editedBranchArm.branchArmUid, this.form).then(resp => {
            bus.$emit('notification', { msg: this.$t('StudyBranchArms.branch_updated') })
            this.close()
          })
        }
      } else {
        arms.editBranchArm(this.selectedStudy.uid, this.editedBranchArm.branchArmUid, this.form).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyBranchArms.branch_updated') })
          this.close()
        })
      }
    },
    close () {
      this.form = {}
      this.$store.commit('form/CLEAR_FORM')
      this.colorHash = null
      this.branchCodeEnable = false
      this.$refs.observer.reset()
      this.$emit('close')
    },
    async cancel () {
      if (this.$store.getters['form/form'] === '' || _isEqual(this.$store.getters['form/form'], JSON.stringify(this.form))) {
        this.close()
      } else {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue')
        }
        if (await this.$refs.form.confirm(this.$t('_global.cancel_changes'), options)) {
          this.close()
        }
      }
    },
    findMaxNuberOfSubjects () {
      this.selectedArm = this.arms.find(e => e.armUid === this.form.armUid)
      return this.selectedArm ? this.selectedArm.numberOfSubjects : 0
    }
  },
  mounted () {
    if (Object.keys(this.editedBranchArm).length !== 0) {
      this.form = JSON.parse(JSON.stringify(this.editedBranchArm))
      this.$set(this.form, 'armUid', this.editedBranchArm.armRoot.armUid)
      if (this.editedBranchArm.colourCode) {
        this.colorHash = this.editedBranchArm.colourCode
      }
      this.$store.commit('form/SET_FORM', this.form)
    }
  },
  watch: {
    editedBranchArm (value) {
      if (Object.keys(value).length !== 0) {
        this.form = JSON.parse(JSON.stringify(value))
        this.$set(this.form, 'armUid', value.armRoot.armUid)
        this.$store.commit('form/SET_FORM', this.form)
      }
    }
  }
}
</script>
