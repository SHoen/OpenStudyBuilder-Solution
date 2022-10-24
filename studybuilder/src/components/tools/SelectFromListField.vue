<template>
<v-row>
  <v-col cols="12" sm="5">
    <header class="primary--text text-uppercase">{{ globalListLabel }}</header>
    <v-card>
      <v-list>
        <v-list-item-group
          v-for="item in items"
          v-model="currentSelectionGlobal"
          :key="item[itemValue]"
          multiple
          >
          <v-list-item :value="item">
            <v-list-item-content>
              <v-list-item-title v-text="item[itemText]"></v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list-item-group>
      </v-list>
    </v-card>
    <div class="d-flex">
      <v-btn
        text
        color="secondary"
        class="text-uppercase"
        @click="selectAll"
        >
        {{ $t('SelectFromListField.select_all') }}
      </v-btn>
      <v-btn
        text
        color="secondary"
        class="text-uppercase"
        @click="deselectAll"
        >
        {{ $t('SelectFromListField.deselect_all') }}
      </v-btn>
    </div>
  </v-col>
  <v-col cols="12" sm="1">
    <v-btn
      icon
      @click="selectItems"
      class="mt-7"
      >
      <v-icon>mdi-arrow-right-thick</v-icon>
    </v-btn>
    <v-btn
      icon
      @click="unselectItems"
      >
      <v-icon>mdi-arrow-left-thick</v-icon>
    </v-btn>
  </v-col>
  <v-col cols="12" sm="5">
    <header class="green--text text-uppercase">{{ selectionListLabel }}</header>
    <v-card>
      <v-list
        style="min-height: 64px;">
        <v-list-item-group
          multiple
          v-model="currentSelectionSelected"
          v-for="(item) in selectedItems"
          :key="item[itemValue]"
          >
          <v-list-item :value="item">
            <v-list-item-content>
              <v-list-item-title>{{ item[itemText] }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list-item-group>
      </v-list>
    </v-card>
    <v-btn
      text
      color="secondary"
      class="text-uppercase"
      @click="removeAll"
      >
      {{ $t('SelectFromListField.remove_all') }}
    </v-btn>
  </v-col>
  <v-col cols="12" sm="1">
    <v-btn
      icon
      class="mt-4"
      @click="moveUp"
      :disabled="disabledMoving"
      >
      <v-icon>mdi-arrow-up-thick</v-icon>
    </v-btn>
    <v-btn
      icon
      @click="moveDown"
      :disabled="disabledMoving"
      >
      <v-icon>mdi-arrow-down-thick</v-icon>
    </v-btn>
  </v-col>
</v-row>
</template>

<script>
import i18n from '@/plugins/i18n'

export default {
  props: {
    items: Array,
    value: Array,
    globalListLabel: {
      type: String,
      default: () => i18n.t('SelectFromListField.global_list_label')
    },
    selectionListLabel: {
      type: String,
      default: () => i18n.t('SelectFromListField.selection_list_label')
    },
    itemText: {
      type: String,
      default: 'text'
    },
    itemValue: {
      type: String,
      default: 'value'
    }
  },
  data () {
    return {
      currentSelectionGlobal: [],
      currentSelectionSelected: [],
      selectedItems: [],
      disabledMoving: true
    }
  },
  methods: {
    disableMoving () {
      if (this.selectedItems.length <= 1 || this.currentSelectionSelected.length === 0 || this.currentSelectionSelected.length > 1) {
        this.disabledMoving = true
      } else {
        this.disabledMoving = false
      }
    },
    selectItems () {
      this.currentSelectionGlobal.forEach(item => {
        if (!this.selectedItems.includes(item)) {
          this.selectedItems.push(item)
        }
      })
      this.currentSelectionGlobal = []
      this.$emit('input', this.selectedItems)
    },
    unselectItems () {
      this.currentSelectionSelected.forEach(item => {
        this.selectedItems = this.selectedItems.filter(selectedItem => selectedItem[this.itemValue] !== item[this.itemValue])
      })
      this.$emit('input', this.selectedItems)
    },
    moveDown () {
      if (this.currentSelectionSelected.length > 1) {
        return
      }
      const itemToMove = this.currentSelectionSelected[0]
      let itemIndex = null
      this.selectedItems.forEach((item, index) => {
        if (item[this.itemValue] === itemToMove[this.itemValue]) {
          itemIndex = index
        }
      })
      let newIndex = 0
      if (itemIndex < this.selectedItems.length - 1) {
        newIndex = itemIndex + 1
      }
      this.selectedItems.splice(itemIndex, 1)
      this.selectedItems.splice(newIndex, 0, itemToMove)
    },
    moveUp () {
      if (this.currentSelectionSelected.length > 1) {
        return
      }
      const itemToMove = this.currentSelectionSelected[0]
      let itemIndex = null
      this.selectedItems.forEach((item, index) => {
        if (item[this.itemValue] === itemToMove[this.itemValue]) {
          itemIndex = index
        }
      })
      let newIndex = this.selectedItems.length - 1
      if (itemIndex > 0) {
        newIndex = itemIndex - 1
      }
      this.selectedItems.splice(itemIndex, 1)
      this.selectedItems.splice(newIndex, 0, itemToMove)
    },
    selectAll () {
      this.currentSelectionGlobal = this.items
    },
    deselectAll () {
      this.currentSelectionGlobal = []
    },
    removeAll () {
      this.selectedItems = []
      this.$emit('input', this.selectedItems)
    }
  },
  watch: {
    currentSelectionSelected: function () {
      this.disableMoving()
    },
    selectedItems: function () {
      this.disableMoving()
    }
  }
}
</script>
