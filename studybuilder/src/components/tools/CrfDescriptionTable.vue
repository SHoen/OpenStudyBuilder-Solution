<template>
<n-n-table
  :headers="headers"
  item-key="uid"
  disable-filtering
  :items="desc"
  hide-export-button
  hide-default-switches>
  <template v-slot:actions="">
    <v-btn
      class="ml-2"
      fab
      dark
      small
      color="primary"
      @click.stop="addLanguage"
      :label="$t('CRFForms.new_translation')"
      data-cy="form-new-translation"
      :disabled="readOnly">
      <v-icon dark>
        mdi-plus
      </v-icon>
    </v-btn>
  </template>
  <template v-slot:item.language="{ index }">
    <v-autocomplete
      v-model="desc[index].language"
      :items="languages"
      :label="$t('CRFForms.language')"
      data-cy="form-language"
      dense
      :clearable="!readOnly"
      class="mt-3"
      item-text="codeSubmissionValue"
      item-value="codeSubmissionValue"
      :readonly="readOnly">
    </v-autocomplete>
  </template>
  <template v-slot:item.name="{ item, index }">
    <div :key="descKey">
      <v-autocomplete
        autocomplete="null"
        :label="$t('CRFForms.name')"
        data-cy="form-displayed-text"
        v-model="desc[index].name"
        :items="descriptions"
        item-text="name"
        return-object
        @change="addExistingDescription(item, index)"
        :clearable="!readOnly"
        v-if="!desc[index].newDesc"
        :readonly="readOnly">
        <template v-slot:no-data>
          <v-row>
            <v-btn
              dark
              small
              color="primary"
              @click.stop="createNewDescription(index)"
              :title="$t('CodelistCreationForm.title')"
              class="mt-3 ml-6 mb-2"
              :disabled="readOnly">
                {{ $t('_global.add_new') }}
            </v-btn>
          </v-row>
        </template>
      </v-autocomplete>
        <v-text-field
          :label="$t('CRFForms.name')"
          data-cy="form-language-name"
          v-model="desc[index].name"
          dense
          :clearable="!readOnly"
          class="mt-5"
          autocomplete="null"
          v-else
          :readonly="readOnly"/>
    </div>
  </template>
  <template v-slot:item.desc="{ index }">
    <vue-editor
      v-model="desc[index].sponsorInstruction"
      data-cy="sponsor-instructions"
      :editor-toolbar="customToolbar"
      :disabled="readOnly"
      v-show="readOnly"/>
    <vue-editor
      v-model="desc[index].sponsorInstruction"
      data-cy="sponsor-instructions"
      :editor-toolbar="customToolbar"
      :placeholder="desc[index].uid ? '' : $t('CRFForms.help_for_sponsor')"
      :disabled="readOnly"
      v-show="!readOnly"/>
  </template>
  <template v-slot:item.inst="{ index }">
    <vue-editor
      v-model="desc[index].instruction"
      data-cy="description-instructions"
      :editor-toolbar="customToolbar"
      :disabled="readOnly"
      v-show="readOnly"/>
    <vue-editor
      v-model="desc[index].instruction"
      data-cy="description-instructions"
      :editor-toolbar="customToolbar"
      :placeholder="desc[index].uid ? '' : $t('CRFForms.instructions')"
      :disabled="readOnly"
      v-show="!readOnly"/>
  </template>
  <template v-slot:item.delete="{ index }">
    <v-btn
      v-if="index !== 0"
      icon
      class="mt-3"
      @click="removeLanguage(index)"
      :disabled="readOnly">
      <v-icon dark>
        mdi-trash-can
      </v-icon>
    </v-btn>
  </template>
</n-n-table>
</template>

<script>
import crfs from '@/api/crfs'
import NNTable from '@/components/tools/NNTable'
import terms from '@/api/controlledTerminology/terms'
import { VueEditor } from 'vue2-editor'

export default {
  components: {
    NNTable,
    VueEditor
  },
  data () {
    return {
      desc: [],
      languages: [],
      headers: [
        { text: this.$t('CRFForms.language'), value: 'language', width: '10%' },
        { text: this.$t('CRFForms.displayed_text'), value: 'name', width: '15%' },
        { text: this.$t('CRFForms.description'), value: 'desc' },
        { text: this.$t('CRFForms.help_for_site'), value: 'inst' },
        { text: '', value: 'delete' }
      ],
      descriptionUids: [],
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }]
      ],
      descriptions: [],
      descKey: 0
    }
  },
  props: {
    editDescriptions: Array,
    readOnly: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    createNewDescription (index) {
      this.desc[index].newDesc = true
      delete this.desc[index].sponsorInstruction
      delete this.desc[index].instruction
      delete this.desc[index].uid
      this.descKey += 1
    },
    addExistingDescription (item, index) {
      if (item.name) {
        this.desc[index].sponsorInstruction = item.name.sponsorInstruction
        this.desc[index].instruction = item.name.instruction
        this.desc[index].uid = item.name.uid
        this.desc[index].name = item.name.name
      }
      this.descKey += 1
    },
    addLanguage () {
      this.desc.push({ language: '' })
    },
    removeLanguage (index) {
      this.desc.splice(index, 1)
    }
  },
  mounted () {
    terms.getAttributesByCodelist('language').then(resp => {
      this.languages = resp.data.items.filter((el) => el.nameSubmissionValue !== 'ENG')
    })
    crfs.getDescriptions().then(resp => {
      this.descriptions = resp.data.items
    })
    if (this.editDescriptions) {
      this.desc = this.editDescriptions
    }
  },
  watch: {
    desc () {
      this.$emit('setDesc', this.desc)
    },
    editDescriptions () {
      if (this.editDescriptions) {
        this.desc = this.editDescriptions
      }
    }
  }
}
</script>
