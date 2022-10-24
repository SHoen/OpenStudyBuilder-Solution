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
        name="Types"
        vid="types"
        >
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.armTypeUid"
              :label="$t('StudyArmsForm.arm_type')"
              :items="armTypes"
              item-text="sponsorPreferredName"
              item-value="termUid"
              data-cy="arm-type"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        name="Name"
        vid="name"
        rules="required|max:200"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('StudyArmsForm.arm_name')"
              data-cy="arm-name"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        name="Short"
        vid="short"
        rules="required|max:20"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.shortName"
              :label="$t('StudyArmsForm.arm_short_name')"
              data-cy="arm-short-name"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        name="Group"
        vid="group"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.randomizationGroup"
              :label="$t('StudyArmsForm.randomisation_group')"
              data-cy="arm-randomisation-group"
              :error-messages="errors"
              clearable
              @blur="enableArmCode"
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        name="Code"
        vid="code"
        rules="max:20"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.code"
              :label="$t('StudyArmsForm.arm_code')"
              data-cy="arm-code"
              :rules="codeRules"
              :error-messages="errors"
              clearable
              :disabled="!armCodeEnable && !isEdit()"
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        name="Number"
        vid="number"
        rules="min_value:1"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.numberOfSubjects"
              :label="$t('StudyArmsForm.planned_number')"
              data-cy="arm-planned-number-of-subjects"
              :error-messages="errors"
              type="number"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        name="Description"
        vid="description"
        rules=""
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.description"
              :label="$t('StudyArmsForm.description')"
              data-cy="arm-description"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <v-text-field
        v-model="branches"
        :label="$t('StudyArmsForm.connected_branches')"
        data-cy="arm-connected-branches"
        clearable
        readonly
        v-if="isEdit()"
        />
      <div class="mt-4">
        <label class="v-label">{{ $t('StudyBranchArms.colour') }}</label>
        <v-color-picker
          v-model="colorHash"
          data-cy="arm-color-hash"
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
import codelists from '@/api/controlledTerminology/terms'
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
      return (Object.keys(this.editedArm).length !== 0)
        ? this.$t('StudyArmsForm.edit_arm')
        : this.$t('StudyArmsForm.add_arm')
    }
  },
  props: {
    editedArm: Object,
    open: Boolean
  },
  data () {
    return {
      form: {},
      helpItems: [
        'StudyArmsForm.arm_name',
        'StudyArmsForm.arm_short_name',
        'StudyArmsForm.arm_type',
        'StudyArmsForm.arm_code',
        'StudyArmsForm.randomisation_group',
        'StudyArmsForm.planned_number',
        'StudyArmsForm.description'
      ],
      armTypes: [],
      colorHash: null,
      editMode: false,
      armCodeEnable: false,
      branches: [],
      codeRules: []
    }
  },
  methods: {
    enableArmCode () {
      if (!this.armCodeEnable) {
        this.$set(this.form, 'code', this.form.randomizationGroup)
        this.armCodeEnable = true
        this.codeRules = [
          v => (v && v.length <= 20) || this.$t('_errors.max_length_reached', { length: '20' })
        ]
      }
    },
    isEdit () {
      return Object.keys(this.editedArm).length !== 0
    },
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      if (Object.keys(this.editedArm).length !== 0) {
        this.edit()
      } else {
        this.create()
      }
    },
    create () {
      if (this.colorHash) {
        this.form.armColour = this.colorHash.hexa
      }
      arms.create(this.selectedStudy.uid, this.form).then(resp => {
        bus.$emit('notification', { msg: this.$t('StudyArmsForm.arm_created') })
        this.close()
      })
    },
    edit () {
      if (this.colorHash) {
        this.form.armColour = this.colorHash.hexa !== undefined ? this.colorHash.hexa : this.colorHash
      }
      arms.edit(this.selectedStudy.uid, this.form, this.editedArm.armUid).then(resp => {
        bus.$emit('notification', { msg: this.$t('StudyArmsForm.arm_updated') })
        this.close()
      })
    },
    close () {
      this.form = {}
      this.colorHash = null
      this.armCodeEnable = false
      this.$refs.observer.reset()
      this.$emit('close')
      this.$store.commit('form/CLEAR_FORM')
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
    }
  },
  mounted () {
    codelists.getByCodelist('armTypes').then(resp => {
      this.armTypes = resp.data.items
    })
    if (Object.keys(this.editedArm).length !== 0) {
      this.form = JSON.parse(JSON.stringify(this.editedArm))
      this.branches = this.form.armConnectedBranchArms.map(el => el.name)
      delete this.form.armConnectedBranchArms
      this.$set(this.form, 'armTypeUid', this.editedArm.armType.termUid)
      if (this.editedArm.armColour) {
        this.colorHash = this.editedArm.armColour
      }
      this.$store.commit('form/SET_FORM', this.form)
    }
  },
  watch: {
    editedArm (value) {
      if (Object.keys(value).length !== 0) {
        this.form = JSON.parse(JSON.stringify(value))
        this.branches = this.form.armConnectedBranchArms.map(el => el.name)
        delete this.form.armConnectedBranchArms
        this.$set(this.form, 'armTypeUid', value.armType.termUid)
        this.$store.commit('form/SET_FORM', this.form)
      }
    }
  }
}
</script>
