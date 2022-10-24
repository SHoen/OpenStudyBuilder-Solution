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
                :label="$t('CRFItems.name') + '*'"
                data-cy="item-name"
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
              :label="$t('CRFItems.oid')"
              data-cy="item-oid"
              v-model="form.oid"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="4">
            <validation-provider
              v-slot="{ errors }"
              rules="required">
              <v-select
                v-model="form.datatype"
                :label="$t('CRFItems.data_type') + '*'"
                data-cy="item-data-type"
                :items="dataTypes"
                item-text="codeSubmissionValue"
                item-value="codeSubmissionValue"
                :error-messages="errors"
                dense
                clearable
                class="mt-3"
                @change="checkIfNumeric()"
                :readonly="readOnly"
                />
            </validation-provider>
          </v-col>
          <v-col cols="4">
            <v-text-field
              :label="$t('CRFItems.length')"
              data-cy="item-length"
              v-model="form.length"
              dense
              clearable
              class="mt-3"
              type="number"
              :readonly="readOnly"
              />
          </v-col>
          <v-col cols="4">
            <v-text-field
              :label="$t('CRFItems.significant_digits')"
              data-cy="item-significant-digits"
              v-model="form.significantDigits"
              dense
              clearable
              class="mt-3"
              type="number"
              :readonly="readOnly"
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2">
            <validation-provider
              rules="">
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
              v-show="readOnly"
              :disabled="readOnly"/>
            <vue-editor
              v-model="engDescription.sponsorInstruction"
              :editor-toolbar="customToolbar"
              :placeholder="$t('CRFForms.help_for_sponsor')"
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
              data-cy="form-oid-name"
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
              v-show="readOnly"
              :disabled="readOnly"/>
            <vue-editor
              v-model="engDescription.instruction"
              :editor-toolbar="customToolbar"
              :placeholder="$t('CRFForms.help_for_site')"
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
            <v-text-field
              :label="$t('CRFItems.sas_name')"
              data-cy="item-sas-name"
              v-model="form.sasFieldName"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              :label="$t('CRFItems.sds_name')"
              data-cy="item-sds-name"
              v-model="form.sdsVarName"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="4">
            <v-select
              v-model="form.origin"
              :label="$t('CRFItems.origin')"
              data-cy="item-origin"
              :items="origins"
              item-text="nciPreferredName"
              item-value="nciPreferredName"
              dense
              clearable
              :readonly="readOnly"/>
          </v-col>
          <v-col cols="8">
            <v-text-field
              :label="$t('CRFItems.comment')"
              data-cy="item-comment"
              v-model="form.comment"
              dense
              clearable
              :readonly="readOnly"
            />
          </v-col>
        </v-row>
        <v-text-field
          :label="$t('CRFItems.prompt')"
          data-cy="item-prompt"
          v-model="form.prompt"
          dense
          clearable
          :readonly="readOnly"
        />
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
              data-cy="item-aliast-context"
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
              data-cy="item-alias-name"
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
            data-cy="item-aliases"
            dense
            clearable
            :item-text="getAliasDisplay"
            item-value="uid"
            :error-messages="errors"
            :readonly="readOnly">
            <template v-slot:selection="{item, index}">
              <div v-if="index === 0">
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
  <template v-slot:step.codelist="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-data-table
        :headers="selectedCodelistHeaders"
        :items="selectedCodelists"
        >
        <template v-slot:item.allowsMultiChoice>
          <v-checkbox
            v-model="form.allowsMultiChoice">
          </v-checkbox>
        </template>
        <template v-slot:item.delete="{ item }">
          <v-btn
            icon
            class="mt-1"
            @click="removeCodelist(item)"
            :disabled="readOnly">
            <v-icon dark>
              mdi-trash-can
            </v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </validation-observer>
  </template>
  <template v-slot:step.codelist.after>
    <v-col class="pt-0 mt-0">
      <n-n-table
        :headers="codelistHeaders"
        item-key="uid"
        :items="codelists"
        has-api
        hide-export-button
        hide-default-switches
        column-data-resource="ct/codelists"
        @filter="fetchCodelists"
        additional-margin>
        <template v-slot:item.add="{ item }">
          <v-btn
            icon
            class="mt-1"
            @click="addCodelist(item)"
            :disabled="readOnly">
            <v-icon dark>
              mdi-plus
            </v-icon>
          </v-btn>
        </template>
      </n-n-table>
    </v-col>
  </template>
  <template v-slot:step.terms="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-data-table
        :headers="selectedTermsHeaders"
        :items="selectedTerms"
        >
        <template v-slot:item.mandatory="{ item }">
          <v-checkbox
            v-model="item.mandatory"
            :readonly="readOnly"
          ></v-checkbox>
        </template>
        <template v-slot:item.delete="{ item }">
          <v-btn
            icon
            class="mt-1"
            @click="removeTerm(item)"
            :disabled="readOnly">
            <v-icon dark>
              mdi-trash-can
            </v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </validation-observer>
  </template>
  <template v-slot:step.terms.after>
    <v-col class="pt-0 mt-0">
      <n-n-table
        :headers="termsHeaders"
        item-key="uid"
        :items="terms"
        hide-export-button
        only-text-search
        hide-default-switches
        additional-margin>
        <template v-slot:item.add="{ item }">
          <v-btn
            icon
            class="mt-1"
            @click="addTerm(item)"
            :disabled="readOnly">
            <v-icon dark>
              mdi-plus
            </v-icon>
          </v-btn>
        </template>
      </n-n-table>
    </v-col>
  </template>
  <template v-slot:step.unit="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <n-n-table
        :headers="unitHeaders"
        item-key="uid"
        disable-filtering
        :items="choosenUnits"
        hide-export-button
        hide-default-switches>
          <template v-slot:actions="">
            <v-btn
              class="ml-2"
              fab
              dark
              small
              color="primary"
              @click.stop="addUnit"
              :label="$t('CRFItemGroups.new_translation')"
              :disabled="readOnly"
            >
              <v-icon dark>
                mdi-plus
              </v-icon>
            </v-btn>
          </template>
          <template v-slot:item.name="{ index }">
            <v-autocomplete
              v-model="choosenUnits[index].name"
              :items="units"
              :label="$t('CRFItems.unit_name')"
              data-cy="item-unit-name"
              dense
              class="mt-3"
              item-text="name"
              item-value="name"
              @change="setUnit(index)"
              return-object
              :readonly="readOnly">
            </v-autocomplete>
          </template>
          <template v-slot:item.mandatory="{ item }">
            <v-checkbox
              v-model="item.mandatory"
              :readonly="readOnly"
            ></v-checkbox>
          </template>
          <template v-slot:item.delete="{ index }">
              <v-btn
                icon
                class="mt-3"
                @click="removeUnit(index)"
                :disabled="readOnly">
                <v-icon dark>
                    mdi-trash-can
                </v-icon>
              </v-btn>
          </template>
      </n-n-table>
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
                :label="$t('CRFItems.change_desc')"
                data-cy="item-change-description"
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
import NNTable from '@/components/tools/NNTable'
import terms from '@/api/controlledTerminology/terms'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import { bus } from '@/main'
import controlledTerminology from '@/api/controlledTerminology'
import constants from '@/constants/libraries'
import CrfDescriptionTable from '@/components/tools/CrfDescriptionTable'
import { VueEditor } from 'vue2-editor'
import { mapGetters } from 'vuex'

export default {
  components: {
    NNTable,
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
        ? (this.readOnly ? this.$t('CRFItems.crf_item') + ' - ' + this.form.name : this.$t('CRFItems.edit_item') + ' - ' + this.form.name)
        : this.$t('CRFItems.add_item')
    }
  },
  data () {
    return {
      helpItems: [],
      form: {
        oid: 'I.',
        aliasUids: [],
        locked: 'no'
      },
      desc: [],
      selectedCodelistHeaders: [
        { text: this.$t('CtCatalogueTable.concept_id'), value: 'codelistUid' },
        { text: this.$t('CtCatalogueTable.cd_name'), value: 'attributes.name' },
        { text: this.$t('CtCatalogueTable.submission_value'), value: 'attributes.submissionValue' },
        { text: this.$t('CtCatalogueTable.nci_pref_name'), value: 'attributes.nciPreferredName' },
        { text: this.$t('CRFItems.multiple_choice'), value: 'allowsMultiChoice' },
        { text: '', value: 'delete' }
      ],
      codelistHeaders: [
        { text: this.$t('CtCatalogueTable.concept_id'), value: 'codelistUid' },
        { text: this.$t('CtCatalogueTable.cd_name'), value: 'attributes.name' },
        { text: this.$t('CtCatalogueTable.submission_value'), value: 'attributes.submissionValue' },
        { text: this.$t('CtCatalogueTable.nci_pref_name'), value: 'attributes.nciPreferredName' },
        { text: '', value: 'add' }
      ],
      unitHeaders: [
        { text: this.$t('CRFItemGroups.name'), value: 'name', width: '25%' },
        { text: this.$t('CRFItems.sponsor_unit'), value: 'oid', width: '20%' },
        { text: this.$t('UnitTable.ucum_unit'), value: 'ucum' },
        { text: this.$t('UnitTable.ct_units'), value: 'terms', width: '30%' },
        { text: this.$t('_global.mandatory'), value: 'mandatory' },
        { text: '', value: 'delete' }
      ],
      termsHeaders: [
        { text: this.$t('_global.uid'), value: 'termUid' },
        { text: this.$t('_global.name'), value: 'name.sponsorPreferredName' },
        { text: '', value: 'add' }
      ],
      selectedTermsHeaders: [
        { text: this.$t('_global.uid'), value: 'termUid' },
        { text: this.$t('_global.name'), value: 'name.sponsorPreferredName' },
        { text: this.$t('_global.mandatory'), value: 'mandatory' },
        { text: '', value: 'delete' }
      ],
      aliases: [],
      alias: {},
      steps: [],
      createSteps: [
        { name: 'form', title: this.$t('CRFItems.item_details') },
        { name: 'description', title: this.$t('CRFItemGroups.description_details'), belowDisplay: true },
        { name: 'alias', title: this.$t('CRFItemGroups.alias_details') }
      ],
      editSteps: [
        { name: 'form', title: this.$t('CRFItems.item_details') },
        { name: 'description', title: this.$t('CRFItemGroups.description_details'), belowDisplay: true },
        { name: 'alias', title: this.$t('CRFItemGroups.alias_details') },
        { name: 'changeDescription', title: this.$t('CRFForms.change_desc') }
      ],
      origins: [],
      units: [],
      choosenUnits: [
        { name: '', mandatory: true }
      ],
      codelists: [],
      selectedCodelists: [],
      options: {},
      total: 0,
      filters: '',
      dataTypes: [],
      descKey: 0,
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }]
      ],
      engDescription: { libraryName: 'Sponsor', language: 'ENG' },
      terms: [],
      selectedTerms: []
    }
  },
  methods: {
    setDesc (desc) {
      this.desc = desc
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    checkIfNumeric () {
      if (this.form.datatype) {
        if ((this.form.datatype.indexOf('INTEGER') !== -1 || this.form.datatype.indexOf('FLOAT') !== -1 || this.form.datatype.indexOf('DOUBLE') !== -1)) {
          this.steps.splice(1, 0, { name: 'unit', title: this.$t('CRFItems.unit_details') })
          this.steps = this.steps.filter(function (obj) {
            return (obj.name !== 'codelist' && obj.name !== 'terms')
          })
        } else if (this.form.datatype.indexOf('STRING') !== -1) {
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'unit'
          })
          this.steps.splice(1, 0, { name: 'codelist', title: this.$t('CRFItems.codelist_details') })
          this.steps.splice(2, 0, { name: 'terms', title: this.$t('CRFItems.codelist_subset') })
        }
        if (this.form.datatype.indexOf('STRING') === -1) {
          this.steps = this.steps.filter(function (obj) {
            return (obj.name !== 'codelist' && obj.name !== 'terms')
          })
        }
        if ((this.form.datatype.indexOf('INTEGER') === -1 && this.form.datatype.indexOf('FLOAT') === -1 && this.form.datatype.indexOf('DOUBLE') === -1)) {
          this.steps = this.steps.filter(function (obj) {
            return obj.name !== 'unit'
          })
        }
      } else {
        this.steps = this.steps.filter(function (obj) {
          return (obj.name !== 'unit' && obj.name !== 'codelist' && obj.name !== 'terms')
        })
      }
      const uniqueSteps = Array.from(new Set(this.steps.map(a => a.name))).map(name => {
        return this.steps.find(a => a.name === name)
      })
      this.steps = uniqueSteps
    },
    close () {
      this.form = {
        oid: 'I.',
        aliasUids: [],
        locked: 'no'
      }
      this.desc = []
      this.choosenUnits = []
      this.selectedCodelists = []
      this.selectedTerms = []
      this.engDescription = { libraryName: 'Sponsor', language: 'ENG' }
      this.$refs.stepper.reset()
      this.$emit('close')
    },
    getCodeListTerms (item) {
      if (item) {
        terms.getTermsByCodelistUid(item.codelistUid).then(resp => {
          this.terms = resp.data.items
          if (this.form.terms) {
            this.form.terms.forEach((el, index) => {
              this.selectedTerms.push(this.terms.find(e => e.termUid === el.termUid))
              if (el.mandatory) {
                this.selectedTerms[index].mandatory = true
              }
            })
          }
          this.terms = this.terms.filter(ar => !this.selectedTerms.find(rm => (rm.termUid === ar.termUid)))
        })
      } else {
        this.terms = []
      }
    },
    addTerm (item) {
      item.mandatory = true
      if (!this.selectedTerms.some(el => el.termUid === item.termUid)) {
        this.selectedTerms.push(item)
        this.terms.splice(this.terms.indexOf(item), 1)
      }
    },
    removeTerm (item) {
      this.selectedTerms = this.selectedTerms.filter(el => el.termUid !== item.termUid)
      this.terms.unshift(item)
    },
    async submit () {
      await this.createOrUpdateDescription()
      this.form.libraryName = constants.LIBRARY_SPONSOR
      if (this.form.oid === 'I.') {
        this.$set(this.form, 'oid', '')
      }
      this.choosenUnits = this.choosenUnits.filter(el => {
        return el.name !== ''
      })
      this.form.unitDefinitions = this.choosenUnits.length === 0 ? [] : this.choosenUnits.map(e => ({ uid: e.uid, mandatory: e.mandatory }))
      if (this.form.datatype !== 'STRING') {
        this.$set(this.form, 'codelistUid', null)
        this.$set(this.form, 'terms', [])
      } else {
        this.form.codelistUid = this.selectedCodelists[0] ? this.selectedCodelists[0].codelistUid : null
        this.$set(this.form, 'terms', this.selectedTerms.map(el => ({ uid: el.termUid, mandatory: el.mandatory })))
      }
      try {
        if (this.isEdit(this.editItem)) {
          this.form.aliasUids = this.form.aliasUids.map(alias => alias.uid ? alias.uid : alias)
          await crfs.updateItem(this.form, this.editItem.uid).then(resp => {
            bus.$emit('notification', { msg: this.$t('CRFItems.item_updated') })
            this.close()
          })
        } else {
          await crfs.createItem(this.form).then(resp => {
            bus.$emit('notification', { msg: this.$t('CRFItems.item_created') })
            this.$emit('linkItem', resp)
            this.close()
          })
        }
      } finally {
        this.$refs.stepper.loading = false
      }
    },
    addUnit () {
      this.choosenUnits.push({ name: '', mandatory: true })
    },
    removeUnit (index) {
      this.choosenUnits.splice(index, 1)
    },
    setUnit (index) {
      this.choosenUnits[index].ucum = this.choosenUnits[index].name.ucum ? this.choosenUnits[index].name.ucum.name : ''
      this.choosenUnits[index].oid = this.choosenUnits[index].name.name
      this.choosenUnits[index].terms = this.choosenUnits[index].name.ctUnits[0] ? this.choosenUnits[index].name.ctUnits[0].name : ''
      this.choosenUnits[index].uid = this.choosenUnits[index].name.uid
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
      this.engDescription = item.descriptions.find(el => el.language === 'ENG')
      this.desc = item.descriptions.filter((el) => el.language !== 'ENG')
      item.unitDefinitions.forEach(e => {
        if (!this.choosenUnits.some(el => el.uid === e.uid)) {
          this.choosenUnits.unshift(
            {
              uid: e.uid,
              oid: e.name,
              name: e.name,
              ucum: e.ucum ? e.ucum.name : '',
              terms: e.ctUnits[0] ? e.ctUnits[0].name : '',
              mandatory: e.mandatory
            }
          )
        }
      })
      if (this.selectedCodelists.length === 0 && item.codelist) {
        this.selectedCodelists.push(
          {
            codelistUid: item.codelist.uid,
            attributes: {
              name: item.codelist.name,
              submissionValue: item.codelist.submissionValue,
              nciPreferredName: item.codelist.preferredTerm
            }
          }
        )
      }
      this.form.changeDescription = ''
      this.checkIfNumeric()
    },
    getAliasDisplay (item) {
      return `${item.context} - ${item.name}`
    },
    isEdit (value) {
      if (value) {
        return Object.keys(value).length !== 0
      }
    },
    fetchCodelists (filters, sort, filtersUpdated) {
      this.filters = filters
      if (this.filtersUpdated) {
        this.options.page = 1
      }
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true,
        library: this.library
      }
      if (this.filters !== undefined) {
        params.filters = this.filters
      }
      controlledTerminology.getCodelists(params).then(resp => {
        this.codelists = resp.data.items.filter(ar => !this.selectedCodelists.find(rm => (rm.codelistUid === ar.codelistUid)))
        this.total = resp.data.total
      })
    },
    addCodelist (item) {
      if (this.selectedCodelists.length === 0) {
        this.selectedCodelists.push(item)
        this.codelists.splice(this.codelists.indexOf(item), 1)
      }
    },
    removeCodelist (item) {
      this.selectedCodelists = []
      this.codelists.unshift(item)
    }
  },
  mounted () {
    this.fetchCodelists()
    terms.getAttributesByCodelist('originType').then(resp => {
      this.origins = resp.data.items
    })
    terms.getAttributesByCodelist('dataType').then(resp => {
      this.dataTypes = resp.data.items
    })
    crfs.getAliases().then(resp => {
      this.aliases = resp.data.items
    })
    this.$store.dispatch('units/fetchUnits').then((resp) => {
      this.units = this.$store.getters['units/units'].items
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
    selectedCodelists (value) {
      this.getCodeListTerms(value[0])
    },
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
          if (value.datatype.indexOf('INTEGER') !== -1 || value.datatype.indexOf('FLOAT') !== -1 || value.datatype.indexOf('DOUBLE') !== -1) {
            this.steps.splice(3, 0, { name: 'unit', title: this.$t('CRFItems.unit_details') })
          }
          if (value.datatype.indexOf('STRING') !== -1) {
            this.steps.splice(1, 0, { name: 'codelist', title: this.$t('CRFItems.codelist_details') })
            this.steps.splice(2, 0, { name: 'terms', title: this.$t('CRFItems.codelist_subset') })
          }
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
        const uniqueSteps = Array.from(new Set(this.steps.map(a => a.name))).map(name => {
          return this.steps.find(a => a.name === name)
        })
        this.steps = uniqueSteps
      },
      immediate: true
    },
    options: {
      handler () {
        this.fetchCodelists()
      },
      deep: true
    }
  }
}
</script>
