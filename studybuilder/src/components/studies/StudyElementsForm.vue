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
    <validation-observer ref="observer">
      <v-row>
        <v-col>
          <validation-provider
            v-slot="{ errors }"
            name=""
            rules=""
            >
            <v-autocomplete
              v-model="form.code"
              :label="$t('StudyElements.el_type')"
              :items="elementTypes"
              item-text="type_name"
              item-value="type"
              :error-messages="errors"
              clearable
              ></v-autocomplete>
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <validation-provider
            v-slot="{ errors }"
            name=""
            rules="required"
            >
            <v-autocomplete
              v-model="form.element_subtype_uid"
              :label="$t('StudyElements.el_sub_type')"
              item-text="subtype_name"
              item-value="subtype"
              :items="elementSubTypes"
              :error-messages="errors"
              clearable
              class="required"
              ></v-autocomplete>
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <validation-provider
            v-slot="{ errors }"
            name=""
            rules="required|max:200"
            >
            <v-text-field
              v-model="form.name"
              :label="$t('StudyElements.el_name')"
              :error-messages="errors"
              clearable
              class="required"
              ></v-text-field>
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <validation-provider
            v-slot="{ errors }"
            name=""
            rules="required|max:20"
            >
            <v-text-field
              v-model="form.short_name"
              :label="$t('StudyElements.el_short_name')"
              :error-messages="errors"
              clearable
              class="required"
              ></v-text-field>
          </validation-provider>
        </v-col>
      </v-row>
      <duration-field
        v-model="form.planned_duration"
        />
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row>
          <v-col>
            <v-textarea
              id="startRule"
              :label="$t('StudyElements.el_start_rule')"
              v-model="form.start_rule"
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
              id="endRule"
              :label="$t('StudyElements.el_end_rule')"
              v-model="form.end_rule"
              rows="1"
              auto-grow
              :error-messages="errors"
              />
          </v-col>
        </v-row>
      </validation-provider>
      <v-row>
        <v-col>
          <validation-provider
            v-slot="{ errors }"
            name=""
            >
            <v-text-field
              v-model="form.description"
              :label="$t('_global.description')"
              :error-messages="errors"
              clearable
              ></v-text-field>
          </validation-provider>
        </v-col>
      </v-row>
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
import _isEqual from 'lodash/isEqual'
import { bus } from '@/main'
import { mapGetters } from 'vuex'
import { studyMetadataFormMixin } from '@/mixins/studyMetadataForm'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import arms from '@/api/arms'
import DurationField from '@/components/tools/DurationField'

export default {
  mixins: [studyMetadataFormMixin],
  components: {
    SimpleFormDialog,
    DurationField
  },
  props: {
    metadata: Object,
    open: Boolean
  },
  data () {
    return {
      form: {
        planned_duration: {}
      },
      helpItems: [
        'StudyElements.el_name',
        'StudyElements.el_short_name',
        'StudyElements.el_sub_type',
        'StudyElements.el_type'
      ],
      data: [],
      allowedConfigs: [],
      colorHash: null
    }
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    title () {
      return this.metadata ? this.$t('StudyElements.edit_el') : this.$t('StudyElements.add_el')
    },
    elementTypes () {
      if (!this.form.element_subtype_uid) {
        return this.allowedConfigs
      } else {
        return this.allowedConfigs.filter(element => element.subtype === this.form.element_subtype_uid)
      }
    },
    elementSubTypes () {
      if (!this.form.code) {
        return this.allowedConfigs
      } else {
        return this.allowedConfigs.filter(element => element.type === this.form.code)
      }
    }
  },
  methods: {
    close () {
      this.form = {}
      this.$emit('close')
      this.colorHash = null
      this.$refs.observer.reset()
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
          this.data = {}
          this.data = this.metadata
          this.close()
        }
      }
    },
    async submit () {
      if (this.colorHash) {
        this.form.element_colour = this.colorHash.hexa !== undefined ? this.colorHash.hexa : this.colorHash
      }
      if (this.metadata) {
        arms.editStudyElement(this.selectedStudy.uid, this.metadata.element_uid, this.form).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyElements.el_edited') })
          this.$refs.form.working = false
          this.close()
        }, _err => {
          this.$refs.form.working = false
        })
      } else {
        arms.addStudyElement(this.selectedStudy.uid, this.form).then(resp => {
          bus.$emit('notification', { msg: this.$t('StudyElements.el_created') })
          this.$refs.form.working = false
          this.close()
        }, _err => {
          this.$refs.form.working = false
        })
      }
    }
  },
  mounted () {
    arms.getStudyElementsAllowedConfigs().then(resp => {
      this.allowedConfigs = resp.data
    })
    if (this.metadata) {
      this.form = this.metadata
      if (this.form.element_colour) {
        this.colorHash = this.form.element_colour
      }
      if (!this.form.planned_duration) {
        this.form.planned_duration = {}
      }
      if (this.metadata.element_subtype) {
        this.$set(this.form, 'element_subtype_uid', this.metadata.element_subtype.term_uid)
      }
      this.$store.commit('form/SET_FORM', this.form)
    }
  },
  watch: {
    metadata () {
      if (this.metadata) {
        this.form = this.metadata
        if (this.form.element_colour) {
          this.colorHash = this.form.element_colour
        }
        if (!this.form.planned_duration) {
          this.form.planned_duration = {}
        }
        if (this.metadata.element_subtype) {
          this.$set(this.form, 'element_subtype_uid', this.metadata.element_subtype.term_uid)
        }
        this.$store.commit('form/SET_FORM', this.form)
      }
    }
  }
}
</script>
