<template>
<simple-form-dialog
  ref="form"
  :title="$t('CrfTree.link') + ' ' + itemsTypeName"
  :help-items="helpItems"
  @close="close"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <v-data-table
      :headers="choosenItemsheaders"
      :items="choosenItems"
      >
      <template v-slot:item.delete="{ item }">
        <v-btn
          icon
          class="mt-1 rightButtons"
          @click="removeItem(item)"
          data-cy="remove-item-link">
          <v-icon dark>
              mdi-trash-can
          </v-icon>
        </v-btn>
      </template>
    </v-data-table>
    <v-col class="pt-0 mt-0">
      <n-n-table
        :headers="availableItemsHeaders"
        item-key="uid"
        :items="items"
        has-api
        hide-export-button
        hide-default-switches
        column-data-resource="ct/codelists"
        additional-margin>
          <template v-slot:item.add="{ item }">
            <v-btn
              icon
              class="mt-1 rightButtons"
              data-cy="add-item-link"
              @click="addItem(item)"
              >
              <v-icon dark>
                  mdi-plus
              </v-icon>
            </v-btn>
          </template>
      </n-n-table>
    </v-col>
  </template>
</simple-form-dialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import crfs from '@/api/crfs'
import constants from '@/constants/parameters'
import NNTable from '@/components/tools/NNTable'

export default {
  components: {
    SimpleFormDialog,
    NNTable
  },
  props: {
    itemToLink: Object,
    itemsType: String,
    open: Boolean
  },
  computed: {
    itemsTypeName () {
      return this.itemsType === 'forms' ? this.$t('CrfTree.forms') : (this.itemsType === 'item-groups' ? this.$t('CrfTree.item_groups') : this.$t('CrfTree.items'))
    }
  },
  data () {
    return {
      helpItems: [],
      items: [],
      choosenItems: [],
      choosenItemsheaders: [
        { text: this.$t('_global.name'), value: 'name' },
        { text: '', value: 'delete' }
      ],
      availableItemsHeaders: [
        { text: this.$t('_global.name'), value: 'name' },
        { text: '', value: 'add' }
      ]
    }
  },
  methods: {
    submit () {
      const payload = []
      this.choosenItems.forEach((el, index) => {
        payload.push({
          uid: el.uid ? el.uid : el,
          orderNumber: index,
          mandatory: el.mandatory ? el.mandatory : false,
          dataEntryRequired: el.dataEntryRequired ? el.dataEntryRequired : 'No',
          sdv: el.sdv ? el.sdv : 'No',
          collectionExceptionConditionOid: el.collectionExceptionConditionOid ? el.collectionExceptionConditionOid : null
        })
      })
      switch (this.itemsType) {
        case 'forms':
          crfs.addFormsToTemplate(payload, this.itemToLink.uid, true).then(resp => {
            this.$emit('close')
          })
          return
        case 'item-groups':
          crfs.addItemGroupsToForm(payload, this.itemToLink.uid, true).then(resp => {
            this.$emit('close')
          })
          return
        case 'items':
          payload.forEach(el => {
            el.keySequence = el.keySequence ? el.keySequence : constants.NULL
            el.methodOid = el.methodOid ? el.methodOid : constants.NULL
            el.imputationMethodOid = el.imputationMethodOid ? el.imputationMethodOid : constants.NULL
            el.role = el.role ? el.role : constants.NULL
            el.roleCodelistOid = el.roleCodelistOid ? el.roleCodelistOid : constants.NULL
          })
          crfs.addItemsToItemGroup(payload, this.itemToLink.uid, true).then(resp => {
            this.$emit('close')
          })
      }
    },
    addItem (item) {
      if (!this.choosenItems.some(el => el.uid === item.uid)) {
        this.choosenItems.push(item)
        this.items = this.items.filter(el => el.uid !== item.uid)
      }
    },
    removeItem (item) {
      this.choosenItems = this.choosenItems.filter(el => el.uid !== item.uid)
      let check = false
      this.items.forEach(el => {
        if (el.name === item.name) {
          check = true
        }
      })
      if (!check) {
        this.items.push(item)
      }
    },
    close () {
      this.form = {}
      this.choosenItems = []
      this.items = []
      this.$emit('close')
    },
    initForm () {
      this.choosenItems = this.itemToLink.forms || this.itemToLink.itemGroups || this.itemToLink.items
      if (this.itemsType) {
        crfs.get(this.itemsType).then((resp) => {
          this.items = resp.data.items
          this.items = this.items.filter(ar => !this.choosenItems.find(rm => (rm.uid === ar.uid)))
        })
      }
    }
  },
  mounted () {
    this.initForm()
  },
  watch: {
    itemToLink () {
      this.initForm()
    }
  }
}
</script>
<style scoped>
  .rightButtons {
    float: right;
  }
</style>
