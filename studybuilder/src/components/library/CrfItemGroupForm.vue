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
              rules="required">
              <v-text-field
                :label="$t('CRFItemGroups.name') + '*'"
                data-cy="item-group-name"
                v-model="form.name"
                :error-messages="errors"
                dense
                clearable
                :readonly="readOnly"
              />
            </validation-provider>
          </v-col>
          <v-col cols="6">
            <v-text-field
              :label="$t('CRFItemGroups.oid')"
              data-cy="item-group-oid"
              v-model="form.oid"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2">
            <validation-provider
              rules="required">
              <v-radio-group
                class="mt-2"
                v-model="form.repeating"
                :label="$t('CRFItemGroups.repeating')"
                :readonly="readOnly"
              >
                <v-radio :label="$t('_global.yes')" value="yes" />
                <v-radio :label="$t('_global.no')" value="no" />
              </v-radio-group>
            </validation-provider>
          </v-col>
          <v-col cols="2">
            <validation-provider
              rules="required">
              <v-radio-group
                class="mt-2"
                v-model="form.locked"
                label="Locked"
                :readonly="readOnly"
              >
                <v-radio :label="$t('_global.yes')" value="yes" />
                <v-radio :label="$t('_global.no')" value="no" />
              </v-radio-group>
            </validation-provider>
          </v-col>
          <v-col cols="8">
            <div class="subtitle-2 text--disabled">{{ $t('CRFForms.help_for_sponsor') }}</div>
            <vue-editor
              v-model="engDescription.sponsorInstruction"
              :editor-toolbar="customToolbar"
              data-cy="crf-item-group-help-for-sponsor"
              v-show="readOnly"
              :disabled="readOnly"/>
            <vue-editor
              v-model="engDescription.sponsorInstruction"
              :editor-toolbar="customToolbar"
              :placeholder="$t('CRFForms.help_for_sponsor')"
              data-cy="crf-item-group-help-for-sponsor"
              v-show="!readOnly"
              :disabled="readOnly"/>
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
              data-cy="crf-item-group-displayed-text"
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
              data-cy="crf-item-group-help-for-site"
              v-show="readOnly"
              :disabled="readOnly"/>
            <vue-editor
              v-model="engDescription.instruction"
              :editor-toolbar="customToolbar"
              :placeholder="$t('CRFForms.help_for_site')"
              data-cy="crf-item-group-help-for-site"
              v-show="!readOnly"
              :disabled="readOnly"/>
          </v-col>
        </v-row>
      </v-card>
      <v-card
        elevation="4"
        class="mx-auto mt-3 pa-4">
        <div class="text-h5 mb-4">{{ $t('CRFForms.annotations') }}</div>
        <v-row>
          <v-col cols="6">
            <v-select
              v-model="form.sdtmDomainUids"
              :label="$t('CRFItemGroups.domain')"
              data-cy="item-group-domain"
              :items="domains"
              :item-text="getDomainDisplay"
              item-value="termUid"
              dense
              clearable
              multiple
              :readonly="readOnly">
              <template v-slot:selection="{index}">
                <div v-if="index === 0">
                  <span>{{ getFirstDomainDisplay() }}</span>
                </div>
                <span
                  v-if="index === 1"
                  class="grey--text text-caption mr-1"
                >
                  (+{{ form.sdtmDomainUids.length - 1 }})
                </span>
              </template>
            </v-select>
          </v-col>
          <v-col cols="6">
            <v-text-field
              :label="$t('CRFItemGroups.sas_dataset')"
              data-cy="item-group-sas-dataset-name"
              v-model="form.sasDatasetName"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2">
            <v-radio-group
              class="mt-2"
              v-model="form.isReferenceData"
              :label="$t('CRFItemGroups.is_referential')"
              :readonly="readOnly"
            >
              <v-radio :label="$t('_global.yes')" value="yes" />
              <v-radio :label="$t('_global.no')" value="no" />
            </v-radio-group>
          </v-col>
          <v-col cols="5">
            <v-select
              v-model="form.origin"
              :label="$t('CRFItemGroups.origin')"
              data-cy="item-group-origin"
              :items="origins"
              item-text="nciPreferredName"
              item-value="nciPreferredName"
              dense
              clearable
              :readonly="readOnly"/>
          </v-col>
          <v-col cols="5">
            <v-select
              v-model="form.role"
              :label="$t('CRFItemGroups.role')"
              data-cy="item-group-role"
              :items="roles"
              item-text="name"
              dense
              clearable
              :readonly="readOnly"/>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-text-field
              :label="$t('CRFItemGroups.purpose')"
              data-cy="item-group-purpose"
              v-model="form.purpose"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              :label="$t('CRFItemGroups.comment')"
              data-cy="item-group-comment"
              v-model="form.comment"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
        </v-row>
      </v-card>
    </validation-observer>
  </template>
  <template v-slot:step.alias="{ step }">
    <validation-observer :ref="`observer_${step}`">
        <div class="mb-5">
          {{ $t('CRFItemGroups.create') }}
        </div>
        <v-row>
          <v-col>
            <v-text-field
              :label="$t('CRFItemGroups.context')"
              data-cy="item-group-alias-context"
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
              :label="$t('CRFItemGroups.name')"
              data-cy="item-group-alias-name"
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
          {{ $t('CRFItemGroups.select') }}
        </div>
        <validation-provider
          v-slot="{ errors }"
          rules=""
          >
          <v-select
            v-model="form.aliasUids"
            :items="aliases"
            multiple
            :label="$t('CRFItemGroups.aliases')"
            dense
            clearable
            :item-text="getAliasDisplay"
            item-value="uid"
            :error-messages="errors"
            :readonly="readOnly">
            <template v-slot:selection="{item, index}">
              <div v-if="index === 0" data-cy="item-group-selected-alias">
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
                data-cy="item-group-change-description"
                v-model="form.changeDescription"
                :error-messages="errors"
                clearable
                :readonly="readOnly"
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
import terms from '@/api/controlledTerminology/terms'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import { bus } from '@/main'
import constants from '@/constants/libraries'
import CrfDescriptionTable from '@/components/tools/CrfDescriptionTable'
import { VueEditor } from 'vue2-editor'
import { mapGetters } from 'vuex'

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
        ? (this.readOnly ? this.$t('CRFItemGroups.item_group') + ' - ' + this.form.name : this.$t('CRFItemGroups.edit_group') + ' - ' + this.form.name)
        : this.$t('CRFItemGroups.add_group')
    }
  },
  data () {
    return {
      helpItems: [],
      form: {
        oid: 'G.',
        repeating: 'no',
        isReferenceData: 'no',
        locked: 'no',
        aliasUids: [],
        sdtmDomainUids: []
      },
      desc: [],
      aliases: [],
      alias: {},
      steps: [],
      createSteps: [
        { name: 'form', title: this.$t('CRFItemGroups.group_details') },
        { name: 'description', title: this.$t('CRFItemGroups.description_details'), belowDisplay: true },
        { name: 'alias', title: this.$t('CRFItemGroups.alias_details') }
      ],
      editSteps: [
        { name: 'form', title: this.$t('CRFItemGroups.group_details') },
        { name: 'description', title: this.$t('CRFItemGroups.description_details'), belowDisplay: true },
        { name: 'alias', title: this.$t('CRFItemGroups.alias_details') },
        { name: 'changeDescription', title: this.$t('CRFForms.change_desc') }
      ],
      origins: [],
      domains: [],
      roles: [],
      engDescription: { libraryName: 'Sponsor', language: 'ENG' },
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }]
      ]
    }
  },
  methods: {
    setDesc (desc) {
      this.desc = desc
    },
    getDomainDisplay (item) {
      return `${item.nciPreferredName} (${item.codeSubmissionValue})`
    },
    getFirstDomainDisplay () {
      return this.domains.find(el => el.termUid === this.form.sdtmDomainUids[0]).nciPreferredName
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    close () {
      this.form = {
        oid: 'G.',
        repeating: 'no',
        isReferenceData: 'no',
        aliasUids: [],
        sdtmDomainUids: [],
        locked: 'no'
      }
      this.desc = []
      this.engDescription = { libraryName: 'Sponsor', language: 'ENG' }
      this.$refs.stepper.reset()
      this.$emit('close')
    },
    async submit () {
      await this.createOrUpdateDescription()
      this.form.libraryName = constants.LIBRARY_SPONSOR
      if (this.form.oid === 'G.') {
        this.$set(this.form, 'oid', '')
      }
      try {
        if (this.isEdit(this.editItem)) {
          this.form.aliasUids = this.form.aliasUids.map(alias => alias.uid ? alias.uid : alias)
          await crfs.updateItemGroup(this.form, this.editItem.uid).then(resp => {
            bus.$emit('notification', { msg: this.$t('CRFItemGroups.group_updated') })
            this.close()
          })
        } else {
          await crfs.createItemGroup(this.form).then(resp => {
            bus.$emit('notification', { msg: this.$t('CRFItemGroups.group_created') })
            this.$emit('linkGroup', resp)
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
          bus.$emit('notification', { msg: this.$t('CRFItemGroups.alias_created') })
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
      this.form.sdtmDomainUids = item.sdtmDomains.map(el => el.uid)
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
    terms.getAttributesByCodelist('originType').then(resp => {
      this.origins = resp.data.items
    })
    terms.getAttributesByCodelist('sdtmDomainAbbreviation').then(resp => {
      this.domains = resp.data.items.sort(function (a, b) {
        return a.nciPreferredName.localeCompare(b.nciPreferredName)
      })
    })
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
