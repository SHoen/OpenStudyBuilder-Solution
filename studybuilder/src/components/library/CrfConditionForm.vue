<template>
<horizontal-stepper-form
  ref="stepper"
  :title="$t('CrfConditionForm.set_condition')"
  :steps="steps"
  @close="close"
  @save="submit"
  :form-observer-getter="getObserver"
  >
  <template v-slot:step.condition="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-card
        elevation="4"
        class="mx-auto pa-4 mb-4">
        <div class="text-h5 mb-4">{{ $t('CRFForms.definition') }}</div>
        <v-row>
          <v-col cols="6">
            <v-text-field
              :label="$t('CRFForms.oid')"
              data-cy="form-oid"
              v-model="form.oid"
              dense
              clearable
            />
          </v-col>
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
              />
            </validation-provider>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="9">
            <div class="subtitle-2 text--disabled">{{ $t('CRFForms.help_for_sponsor') }}</div>
            <vue-editor
              v-model="engDescription.sponsorInstruction"
              :editor-toolbar="customToolbar"
              :placeholder="$t('CRFForms.help_for_sponsor')"/>
          </v-col>
        </v-row>
      </v-card>
    </validation-observer>
  </template>
  <template v-slot:step.description="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <crf-description-table @setDesc="setDesc" :editDescriptions="desc" :key="descKey"/>
    </validation-observer>
  </template>
  <template v-slot:step.expression="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col>
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
              <v-text-field
                :label="$t('CrfConditionForm.context')"
                v-model="form.formalExpressions[0].context"
                :error-messages="errors"
                dense
                clearable
                class="mt-3"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-textarea
              :label="$t('CrfConditionForm.formal_expression')"
              v-model="form.formalExpressions[0].expression"
              :error-messages="errors"
              dense
              clearable
              class="mt-6"
            />
          </validation-provider>
        </v-col>
      </v-row>
      <div v-for="(expression, index) in expressionsArray" :key="expression.index">
        <div v-if="!form.uid">
          <v-row>
            <v-col>
              <v-autocomplete
                :label="$t('CrfConditionForm.nested_element')"
                :items="nestedElements"
                v-model="expressionsArray[index].elementType"
                dense
                clearable
                @change="setFormalExpression()"/>
            </v-col>
            <v-col>
              <v-autocomplete
                v-model="expressionsArray[index].element"
                :items="expressionsArray[index].elementType === 'Form' ? crfForms : (expressionsArray[index].elementType === 'Item Group' ? crfGroups : crfItems)"
                :disabled="!expressionsArray[index].elementType"
                item-text="name"
                item-value="oid"
                return-object
                dense
                clearable
                @change="setFormalExpression()"/>
            </v-col>
            <v-col cols="2">
              <v-autocomplete
                :label="$t('CrfConditionForm.separator')"
                :items="separators"
                v-model="expressionsArray[index].separator"
                dense
                clearable
                @change="setFormalExpression()"/>
            </v-col>
          </v-row>
          <v-row :key="key" v-show="expressionsArray[index].elementType === 'Item' && expressionsArray[index].element && expressionsArray[index].element.codelist">
            <v-col>
              {{ $t('CrfConditionForm.select_value') }}
            </v-col>
            <v-col>
              <v-autocomplete
                label="Value"
                :items="expressionsArray[index].terms"
                v-model="expressionsArray[index].value"
                item-text="name.sponsorPreferredName"
                item-value="name.sponsorPreferredName"
                dense
                clearable
                @change="setFormalExpression()"
                :key="key"
                :loading="!expressionsArray[index].terms"
                />
            </v-col>
          </v-row>
        </div>
      </div>
      <v-btn
        data-cy='create-new-sponsor-values'
        color="primary"
        icon
        @click="addExpression"
        v-if="!form.uid"
        >
        <v-icon>mdi-plus-circle-outline</v-icon>
      </v-btn>
    </validation-observer>
  </template>
</horizontal-stepper-form>
</template>

<script>
import crfs from '@/api/crfs'
import CrfDescriptionTable from '@/components/tools/CrfDescriptionTable'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import constants from '@/constants/libraries'
import terms from '@/api/controlledTerminology/terms'
import { VueEditor } from 'vue2-editor'
import { mapGetters } from 'vuex'

export default {
  components: {
    HorizontalStepperForm,
    CrfDescriptionTable,
    VueEditor
  },
  props: {
    itemToLink: Object,
    crfForms: Array,
    crfGroups: Array,
    crfItems: Array,
    crfGroup: Object
  },
  computed: {
    ...mapGetters({
      userData: 'app/userData'
    })
  },
  data () {
    return {
      helpItems: [],
      form: {
        oid: 'C.',
        formalExpressions: [
          {
            libraryName: 'Sponsor',
            context: 'XPath'
          }
        ],
        aliasUids: []
      },
      descriptionUids: [],
      steps: [
        { name: 'condition', title: this.$t('CrfConditionForm.condition') },
        { name: 'description', title: this.$t('CRFForms.description_details'), belowDisplay: true },
        { name: 'expression', title: this.$t('CrfConditionForm.formal_expression') }
      ],
      desc: [],
      nestedElements: ['Form', 'Item Group', 'Item'],
      expressionsArray: [{ index: 0 }],
      separators: ['AND', 'OR'],
      key: 0,
      terms: [],
      descKey: 0,
      engDescription: { libraryName: 'Sponsor', language: 'ENG' },
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }]
      ]
    }
  },
  mounted () {
    this.initForm()
    if (!this.userData.multilingual) {
      this.steps = this.steps.filter(function (obj) {
        return obj.name !== 'description'
      })
    } else {
      this.steps.splice(1, 0, { name: 'description', title: this.$t('CRFForms.description_details'), belowDisplay: true })
    }
    const uniqueSteps = Array.from(new Set(this.steps.map(a => a.name))).map(name => {
      return this.steps.find(a => a.name === name)
    })
    this.steps = uniqueSteps
  },
  methods: {
    getCodelistTerms (index, codelist) {
      if (codelist) {
        const params = {}
        params.codelist_uid = codelist.uid
        terms.getAll(params).then(resp => {
          this.expressionsArray[index].terms = resp.data.items
          this.key += 1
        })
      } else {
        this.expressionsArray[index].terms = []
      }
    },
    setFormalExpression () {
      const itemDef = 'ItemDef'
      const itemGroupDef = 'ItemGroupDef'
      const formDef = 'FormDef'
      const oid = '[@OID='
      const value = '[@Value='
      this.form.formalExpressions[0].expression = '../'
      this.expressionsArray.forEach((el, index) => {
        if (el.elementType === 'Form' && el.element) {
          this.form.formalExpressions[0].expression += formDef + oid + el.element.oid + (el.separator ? `] ${el.separator} ../` : ']/')
        }
        if (el.elementType === 'Item Group' && el.element) {
          this.form.formalExpressions[0].expression += itemGroupDef + oid + el.element.oid + (el.separator ? `] ${el.separator} ../` : ']/')
        }
        if (el.elementType === 'Item' && el.element) {
          this.form.formalExpressions[0].expression += itemDef + oid + el.element.oid + ']' + value + el.value + (el.separator ? `] ${el.separator} ../` : ']')
          this.getCodelistTerms(index, el.element.codelist)
        }
      })
      if (this.form.formalExpressions[0].expression[this.form.formalExpressions[0].length - 1] === '/') {
        this.form.formalExpressions[0].expression = this.form.formalExpressions[0].slice(0, -1)
      }
    },
    addExpression () {
      this.expressionsArray.push({ index: this.expressionsArray.length })
    },
    setDesc (desc) {
      this.desc = desc
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    close () {
      this.form = {
        oid: 'C.',
        formalExpressions: [
          {
            libraryName: 'Sponsor',
            context: 'XPath'
          }
        ],
        aliasUids: []
      }
      this.desc = []
      this.engDescription = { libraryName: 'Sponsor', language: 'ENG' }
      this.expressionsArray = [{ index: 0 }]
      this.descKey += 1
      this.$refs.stepper.reset()
      this.$emit('cancel')
    },
    async submit () {
      await this.createOrUpdateDescription()
      this.form.libraryName = constants.LIBRARY_SPONSOR
      if (this.form.oid === 'C.') {
        this.$set(this.form, 'oid', '')
      }
      try {
        if (this.form.uid) {
          this.form.formalExpressions[0].changeDescription = ''
          crfs.editCondition(this.form.uid, this.form).then(resp => {
            this.close()
            this.$emit('close')
          })
        } else if (this.itemToLink.parentFormUid) {
          await crfs.createCondition(this.form).then(resp => {
            const data = [this.itemToLink]
            this.$set(data[0], 'collectionExceptionConditionOid', resp.data.oid)
            crfs.addItemGroupsToForm(data, this.itemToLink.parentFormUid, false).then(resp => {
              this.close()
              this.$emit('close')
            })
          })
        } else if (this.itemToLink.parentGroupUid) {
          await crfs.createCondition(this.form).then(resp => {
            const data = [this.itemToLink]
            this.$set(data[0], 'collectionExceptionConditionOid', resp.data.oid)
            crfs.addItemsToItemGroup(data, this.itemToLink.parentGroupUid, false).then(resp => {
              this.close()
              this.$emit('close')
            })
          })
        }
      } finally {
        this.$refs.stepper.loading = false
      }
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
    initForm () {
      if (this.itemToLink.collectionExceptionConditionOid && this.itemToLink.collectionExceptionConditionOid !== 'null' && this.itemToLink.collectionExceptionConditionOid !== 'none') {
        const data = {}
        data.filters = `{"oid":{ "v": ["${this.itemToLink.collectionExceptionConditionOid}"], "op": "co" }}`
        crfs.getConditionByOid(data).then(resp => {
          this.engDescription = resp.data.items[0].descriptions.find(el => el.language === 'ENG')
          this.desc = resp.data.items[0].descriptions.filter((el) => el.language !== 'ENG')
          this.form = resp.data.items[0]
          this.form.aliasUids = []
          this.descKey += 1
        })
      }
    }
  },
  watch: {
    itemToLink (value) {
      this.initForm()
      if (!this.userData.multilingual) {
        this.steps = this.steps.filter(function (obj) {
          return obj.name !== 'description'
        })
      } else {
        this.steps.splice(1, 0, { name: 'description', title: this.$t('CRFForms.description_details'), belowDisplay: true })
      }
      const uniqueSteps = Array.from(new Set(this.steps.map(a => a.name))).map(name => {
        return this.steps.find(a => a.name === name)
      })
      this.steps = uniqueSteps
    }
  }
}
</script>
