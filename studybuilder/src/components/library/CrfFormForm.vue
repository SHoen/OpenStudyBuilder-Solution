<template>
<horizontal-stepper-form
  ref="stepper"
  :title="title"
  :steps="steps"
  @close="close"
  @save="submit"
  :form-observer-getter="getObserver"
  >
  <template v-slot:step.form="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-card
        elevation="4"
        class="mx-auto pa-4">
        <div class="text-h5 mb-4">{{ $t('CRFForms.definition') }}</div>
        <v-row>
          <v-col cols="6">
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-text-field
                :label="$t('CRFForms.name') + '*'"
                data-cy="form-oid-name"
                v-model="form.name"
                :error-messages="errors"
                dense
                clearable
                :readonly="readOnly"
              />
            </validation-provider>
          </v-col>
          <v-col cols="6">
            <validation-provider
              v-slot="{ errors }"
              >
              <v-text-field
                :label="$t('CRFForms.oid')"
                data-cy="form-oid"
                v-model="form.oid"
                :error-messages="errors"
                dense
                clearable
                :readonly="readOnly"
              />
            </validation-provider>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="3">
            <validation-provider
              rules="required"
              >
              <v-radio-group
                v-model="form.repeating"
                :label="$t('CRFForms.repeating')"
                :readonly="readOnly"
              >
                <v-radio :label="$t('_global.yes')" value="yes" />
                <v-radio :label="$t('_global.no')" value="no" />
              </v-radio-group>
            </validation-provider>
          </v-col>
          <v-col cols="9">
            <div class="subtitle-2 text--disabled">{{ $t('CRFForms.help_for_sponsor') }}</div>
            <vue-editor
              v-model="engDescription.sponsorInstruction"
              :editor-toolbar="customToolbar"
              :disabled="readOnly"
              data-cy="help-for-sponsor"
              v-show="readOnly"/>
            <vue-editor
              v-model="engDescription.sponsorInstruction"
              :editor-toolbar="customToolbar"
              :disabled="readOnly"
              :placeholder="$t('CRFForms.help_for_sponsor')"
              v-show="!readOnly"
              data-cy="help-for-sponsor"/>
          </v-col>
        </v-row>
      </v-card>
      <v-card
        elevation="4"
        class="mx-auto mt-3 pa-4">
        <div class="text-h5 mb-4">{{ $t('CRFForms.display') }}</div>
        <v-row>
          <v-col cols="3">
            <v-text-field
              :label="$t('CRFForms.displayed_text')"
              data-cy="form-oid-displayed-text"
              v-model="engDescription.name"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
          <v-col cols="9">
            <div class="subtitle-2 text--disabled">{{ $t('CRFForms.help_for_site') }}</div>
            <vue-editor
              v-model="engDescription.instruction"
              :editor-toolbar="customToolbar"
              :disabled="readOnly"
              v-show="readOnly"
              data-cy="form-help-for-site"/>
            <vue-editor
              v-model="engDescription.instruction"
              :editor-toolbar="customToolbar"
              :disabled="readOnly"
              :placeholder="$t('CRFForms.help_for_site')"
              v-show="!readOnly"
              data-cy="form-help-for-site"/>
          </v-col>
        </v-row>
      </v-card>
    </validation-observer>
  </template>
  <template v-slot:step.alias="{ step }">
    <validation-observer :ref="`observer_${step}`">
        <div class="mb-5">
          {{ $t('CRFForms.create') }}
        </div>
        <v-row>
          <v-col>
            <v-text-field
              :label="$t('CRFForms.context')"
              data-cy="form-context"
              v-model="alias.context"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="10">
            <v-text-field
              :label="$t('CRFForms.name')"
              data-cy="form-alias-name"
              v-model="alias.name"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
          <v-col>
            <v-btn
              data-cy="save-button"
              color="secondary"
              @click="createAlias"
              class="mr-2"
              :disabled="readOnly"
              >
              {{ $t('_global.save') }}
            </v-btn>
          </v-col>
        </v-row>
        <div class="mb-5">
          {{ $t('CRFForms.select') }}
        </div>
        <validation-provider
          v-slot="{ errors }"
          rules=""
          >
          <v-select
            v-model="form.aliasUids"
            :items="aliases"
            multiple
            :label="$t('CRFForms.aliases')"
            dense
            clearable
            :item-text="getAliasDisplay"
            item-value="uid"
            :error-messages="errors"
            :readonly="readOnly">
            <template v-slot:selection="{item, index}">
              <div v-if="index === 0" data-cy="form-aliases">
                <span>{{ item.name }}</span>
              </div>
              <span
                v-if="index === 1"
                class="grey--text text-caption"
              >
                (+{{ form.aliasUids.length -1 }})
              </span>
            </template>
          </v-select>
        </validation-provider>
    </validation-observer>
  </template>
  <template v-slot:step.description="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <crf-description-table
        @setDesc="setDesc"
        :editDescriptions="desc"
        :readOnly="readOnly"/>
    </validation-observer>
  </template>
  <template v-slot:step.changeDescription="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col>
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
              <v-text-field
                :label="$t('CRFForms.change_desc')"
                data-cy="form-change-description"
                v-model="form.changeDescription"
                :error-messages="errors"
                clearable
              />
          </validation-provider>
        </v-col>
      </v-row>
    </validation-observer>
  </template>
</horizontal-stepper-form>
</template>

<script>
import crfs from '@/api/crfs'
import CrfDescriptionTable from '@/components/tools/CrfDescriptionTable'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import { bus } from '@/main'
import constants from '@/constants/libraries'
import { mapGetters } from 'vuex'
import { VueEditor } from 'vue2-editor'

export default {
  components: {
    HorizontalStepperForm,
    CrfDescriptionTable,
    VueEditor
  },
  props: {
    editItem: {},
    readOnly: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    ...mapGetters({
      userData: 'app/userData'
    }),
    title () {
      return (this.isEdit(this.editItem))
        ? (this.readOnly ? this.$t('CRFForms.crf_form') + ' - ' + this.form.name : this.$t('CRFForms.edit_form') + ' - ' + this.form.name)
        : this.$t('CRFForms.add_form')
    }
  },
  data () {
    return {
      helpItems: [],
      form: {
        oid: 'F.',
        repeating: 'no',
        aliasUids: []
      },
      aliases: [],
      alias: {},
      descriptionUids: [],
      createSteps: [
        { name: 'form', title: this.$t('CRFForms.form_details') },
        { name: 'description', title: this.$t('CRFForms.description_details'), belowDisplay: true },
        { name: 'alias', title: this.$t('CRFForms.alias_details') }
      ],
      editSteps: [
        { name: 'form', title: this.$t('CRFForms.form_details') },
        { name: 'description', title: this.$t('CRFForms.description_details'), belowDisplay: true },
        { name: 'alias', title: this.$t('CRFForms.alias_details') },
        { name: 'changeDescription', title: this.$t('CRFForms.change_desc') }
      ],
      desc: [],
      steps: [],
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }]
      ],
      engDescription: { libraryName: 'Sponsor', language: 'ENG' }
    }
  },
  methods: {
    setDesc (desc) {
      this.desc = desc
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    close () {
      this.form = {
        oid: 'F.',
        repeating: 'no',
        aliasUids: []
      }
      this.engDescription = { libraryName: 'Sponsor', language: 'ENG' }
      this.desc = []
      this.$refs.stepper.reset()
      this.$emit('close')
    },
    async submit () {
      await this.createOrUpdateDescription()
      this.form.libraryName = constants.LIBRARY_SPONSOR
      if (this.form.oid === 'F.') {
        this.$set(this.form, 'oid', '')
      }
      try {
        if (this.isEdit(this.editItem)) {
          this.form.aliasUids = this.form.aliasUids.map(alias => alias.uid ? alias.uid : alias)
          await crfs.updateForm(this.form, this.editItem.uid).then(resp => {
            bus.$emit('notification', { msg: this.$t('CRFForms.form_updated') })
            this.close()
          })
        } else {
          await crfs.createForm(this.form).then(resp => {
            bus.$emit('notification', { msg: this.$t('CRFForms.form_created') })
            this.$emit('linkForm', resp)
            this.close()
          })
        }
      } finally {
        this.$refs.stepper.loading = false
      }
    },
    async createAlias () {
      this.alias.libraryName = constants.LIBRARY_SPONSOR
      await crfs.createAlias(this.alias).then(resp => {
        this.form.aliasUids.push(resp.data.uid)
        crfs.getAliases().then(resp => {
          this.aliases = resp.data.items
          this.alias = {}
          bus.$emit('notification', { msg: this.$t('CRFForms.alias_created') })
        })
      })
    },
    async createOrUpdateDescription () {
      const descArray = []
      this.desc.forEach(e => {
        if (e.uid) {
          descArray.push(e)
        } else {
          e.libraryName = constants.LIBRARY_SPONSOR
          descArray.push(e)
        }
      })
      if (!this.engDescription.name) {
        this.engDescription.name = this.form.name
      }
      descArray.push(this.engDescription)
      this.form.descriptions = descArray
    },
    initForm (item) {
      this.form.aliasUids = item.aliases
      this.form.changeDescription = ''
      this.engDescription = item.descriptions.find(el => el.language === 'ENG')
      this.desc = item.descriptions.filter((el) => el.language !== 'ENG')
    },
    getAliasDisplay (item) {
      return `${item.context} - ${item.name}`
    },
    isEdit (value) {
      return Object.keys(value).length !== 0
    }
  },
  mounted () {
    crfs.getAliases().then(resp => {
      this.aliases = resp.data.items
    })
    if (this.isEdit(this.editItem)) {
      this.steps = this.readOnly ? this.createSteps : this.editSteps
      this.form = this.editItem
      this.initForm(this.editItem)
    } else {
      this.steps = this.createSteps
    }
    if (!this.userData.multilingual) {
      this.steps = this.steps.filter(function (obj) {
        return obj.name !== 'description'
      })
    }
  },
  watch: {
    userData: {
      handler () {
        if (!this.userData.multilingual) {
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'description'
          })
        } else {
          this.steps = this.createSteps
        }
      }
    },
    editItem: {
      handler (value) {
        if (this.isEdit(value)) {
          this.steps = this.readOnly ? this.createSteps : this.editSteps
          this.form = value
          this.initForm(value)
        } else {
          this.steps = this.createSteps
        }
        if (!this.userData.multilingual) {
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'description'
          })
        }
      },
      immediate: true
    }
  }
}
</script>
