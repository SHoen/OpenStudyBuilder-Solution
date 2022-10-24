<template>
<v-card>
  <v-card-title>
    {{ $t('CrfDuplicationForm.duplicate') }}
  </v-card-title>
  <v-card-text>
    <v-row>
      <v-col cols="2" v-if="type !== crfTypes.ITEM">
        <v-checkbox
          v-model="relations"
          :label="$t('CrfDuplicationForm.include')"
          class="mt-6 ml-2"/>
      </v-col>
      <v-col cols="4" v-if="type !== crfTypes.ITEM">
        <odm-references-tree
        :item="item"
        :type="type"
        no-title
        no-actions
        :full-data="false"
        :open-all="relations"/>
      </v-col>
      <v-col :cols="type === crfTypes.ITEM ? 12 : 6">
        {{ $t('CrfDuplicationForm.attributes') }}
        <v-row>
          <v-col cols="5">
            <v-text-field
              :label="$t('_global.name')"
              v-model="name"
              dense
              clearable
              class="mt-6"
            />
          </v-col>
          <v-col cols="5">
            <v-text-field
              :label="$t('_global.oid')"
              v-model="oid"
              dense
              clearable
              class="mt-6"
            />
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-card-text>
  <v-card-actions>
    <v-spacer></v-spacer>
    <v-btn
      class="primary"
      @click="save()"
      >
      {{ $t('_global.save') }}
    </v-btn>
    <v-btn
      class="secondary-btn"
      color="white"
      @click="close()"
      >
      {{ $t('_global.close') }}
    </v-btn>
  </v-card-actions>
</v-card>
</template>

<script>
import OdmReferencesTree from '@/components/library/OdmReferencesTree'
import crfs from '@/api/crfs'
import crfTypes from '@/constants/crfTypes'

export default {
  components: {
    OdmReferencesTree
  },
  props: {
    open: Boolean,
    item: Object,
    type: String
  },
  data () {
    return {
      relations: false,
      name: '',
      oid: '',
      form: {}
    }
  },
  created () {
    this.crfTypes = crfTypes
  },
  methods: {
    close () {
      this.$emit('close')
    },
    save () {
      this.form = this.item
      this.$set(this.form, 'name', this.name)
      this.$set(this.form, 'oid', this.oid)
      if (this.type === crfTypes.TEMPLATE) {
        crfs.createTemplate(this.form).then(resp => {
          if (this.relations) {
            crfs.addFormsToTemplate(this.item.forms, resp.data.uid, true).then(resp => {
            })
          }
          this.close()
        })
      } else if (this.type === crfTypes.FORM) {
        this.form.aliasUids = this.form.aliases.map(alias => alias.uid)
        crfs.createForm(this.form).then(resp => {
          if (this.relations) {
            crfs.addItemGroupsToForm(this.item.itemGroups, resp.data.uid, true)
          }
          this.close()
        })
      } else if (this.type === crfTypes.GROUP) {
        this.form.aliasUids = this.form.aliases.map(alias => alias.uid)
        this.form.sdtmDomainUids = this.form.sdtmDomains.map(sdtm => sdtm.uid)
        crfs.createItemGroup(this.form).then(resp => {
          if (this.relations) {
            crfs.addItemsToItemGroup(this.item.items, resp.data.uid, true)
          }
          this.close()
        })
      } else {
        this.form.aliasUids = this.form.aliases.map(alias => alias.uid)
        if (this.form.codelist) {
          this.form.codelistUid = this.form.codelist
        }
        this.form.terms.forEach(term => {
          term.uid = term.termUid
          delete term.termUid
        })
        crfs.createItem(this.form).then(resp => {
          this.close()
        })
      }
    }
  }
}
</script>
