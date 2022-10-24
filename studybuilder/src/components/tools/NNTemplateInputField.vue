<template>
<div class="template-field">
  <vue-editor
    data-cy="input-field"
    ref="editor"
    id="editor"
    :value="value"
    @input="onInputChanged"
    @blur="onBlur"
    :editor-toolbar="customToolbar"
    :placeholder="label"
    >
  </vue-editor>
  <div v-if="!errorMessages.length" class="mt-1 v-messages theme--light">
    <div class="v-messages__wrapper">
      <div class="v-messages__message">
        {{ hint }}
      </div>
    </div>
  </div>
  <div v-else class="mt-1 v-messages theme--light error--text">
    <div class="v-messages__wrapper">
      <div class="v-messages__message">
        {{ errorMessages.join(', ') }}
      </div>
    </div>
  </div>
  <div
    ref="types"
    class="types"
    :style="`width: ${width}px;`"
    v-if="showDropDown && filteredItems.length > 0"
    >
    <v-list
      class="list"
      >
      <v-list-item
        v-for="(item, index) in filteredItems"
        :key="index"
        @click="selectItem(item)"
        :class="selectionIndex === index ? 'selected' : ''"
        >
        {{ (encloseParametersInDropdown ? prefix + item.name + postfix : item.name) }}
        <span
          v-if="item.values !== undefined && item.values.length > 0"
          >(e.g. {{ item.values.slice(0, 3).map(el => el.name).join(', ') }} ...)</span>
      </v-list-item>
    </v-list>
  </div>
</div>
</template>

<script>
import i18n from '@/plugins/i18n'
import { VueEditor, Quill } from 'vue2-editor'

const Delta = Quill.import('delta')

export default {
  components: {
    VueEditor
  },
  props: {
    value: String,
    label: String,
    items: {
      type: Array,
      default: () => []
    },
    hint: {
      type: String,
      default: () => i18n.t('NNTemplateInputField.default_hint')
    },
    prefix: {
      type: String,
      default: '['
    },
    postfix: {
      type: String,
      default: ']'
    },
    showDropDownEarly: {
      type: Boolean,
      default: true
    },
    encloseParametersInDropdown: {
      type: Boolean,
      default: true
    },
    errorMessages: {
      type: Array,
      required: false
    }
  },
  data: () => ({
    searchTerm: null,
    // keeps track of the selected item from the drop down menu
    // refers to the computed filteredItems
    selectionIndex: 0,
    showDropDown: false,
    filteredItems: [],
    width: 500,
    customToolbar: [
      ['bold', 'italic', 'underline'],
      [{ script: 'sub' }, { script: 'super' }],
      [{ list: 'ordered' }, { list: 'bullet' }]
    ]
  }),
  mounted () {
    this.focusInput()
    this.$refs.editor.quill.root.addEventListener('dblclick', this.onDoubleClick)
    window.addEventListener('resize', this.onResize)
  },
  updated () {
    this.$root.$nextTick(() => {
      this.updateMinWidthProperty()
    })
  },
  watch: {
    searchTerm (val) {
      this.updateFilteredItems()
    }
  },
  methods: {
    updateFilteredItems () {
      if (this.searchTerm === null || this.searchTerm === undefined || this.searchTerm === '' || this.searchTerm === this.prefix || this.searchTerm === '\n') {
        this.filteredItems = this.items
      } else {
        this.filteredItems = this.items.filter(item => {
          return item.name.toString().toLowerCase().indexOf(this.searchTerm.toLowerCase()) !== -1
        })
      }
    },
    onInputChanged (input) {
      setTimeout(() => {
        const textContent = this.$refs.editor.quill.getText()
        // We receive HTML but we only want text content
        this.updateSearchTerm(textContent)
        this.$emit('input', input)
      }, 100)
    },
    getCaretPosition () {
      return this.getSelectionStart()
    },
    setCaretPosition (pos) {
      const newRange = document.createRange()
      const selection = window.getSelection()
      const node = this.$refs.input.childNodes[0]
      newRange.setStart(node, node && pos > node.length ? 0 : pos)
      newRange.collapse(true)
      selection.removeAllRanges()
      selection.addRange(newRange)
    },
    getPosition () {
      const range = this.$refs.editor.quill.getSelection()
      const position = { start: 0, end: 0 }
      if (range) {
        position.start = range.index
        if (range.length) {
          position.end = range.index + range.length
        } else {
          position.end = range.index
        }
      }
      return position
    },
    getSelectionStart () {
      return this.getPosition().start
    },
    getSelectionEnd () {
      return this.getPosition().end
    },
    updateSearchTerm (input) {
      if (input === null || input === undefined || typeof input !== 'string') {
        return
      }

      const searchTerm = this.getSearchTermFromString(input)

      let showDropDown = this.showDropDownEarly
      if (searchTerm.startsWith(this.prefix)) {
        this.searchTerm = searchTerm.substring(this.prefix.length)
        showDropDown = true
      } else {
        this.searchTerm = searchTerm
      }

      this.selectionIndex = 0
      this.showDropDown = showDropDown
    },
    getSearchTermFromString (s) {
      const textToCaret = s.substring(0, this.getCaretPosition())

      const lastCharacter = textToCaret.substring(textToCaret.length - 1)
      const lastCharacterCode = lastCharacter.charCodeAt(lastCharacter.length - 1)

      // 160 = non breaking 'space' character (cf. HTMLs &nbsp;)
      // 32 = the simple space character
      if (lastCharacterCode === 160 || lastCharacterCode === 32 || lastCharacterCode === 10) {
        return ''
      }

      const arr = textToCaret.split(' ')
      return arr[arr.length - 1]
    },
    getWordRightFromCaret (s) {
      const textRightFromCaret = s.substring(this.getCaretPosition())

      const firstCharacter = textRightFromCaret.substring(0, 1)
      const firstCharacterCode = firstCharacter.charCodeAt(0)

      // 160 = non breaking 'space' character (cf. HTMLs &nbsp;)
      // 32 = the simple space character
      if (firstCharacterCode === 160 || firstCharacterCode === 32 || firstCharacterCode === 10) {
        return ''
      }

      const arr = textRightFromCaret.split(/\s/)
      return arr[0]
    },
    onKeyDown (e) {
      const keyCode = e.keyCode

      if (keyCode === 40 || keyCode === 34) {
        // on arrow down or page down
        if (!this.showDropDown) {
          this.searchTerm = ''
          this.showDropDown = true
        } else {
          this.increaseSelectionIndex()
        }
        e.preventDefault()
      } else if (keyCode === 38 || keyCode === 33) {
        // on arrow up or page up
        if (!this.showDropDown) {
          this.searchTerm = ''
          this.showDropDown = true
        } else {
          this.decreaseSelectionIndex()
        }
        e.preventDefault()
      } else if (keyCode === 13 || keyCode === 9) {
        // on enter or tab
        this.selectItem(this.filteredItems[this.selectionIndex])
        e.preventDefault()
      } else if (keyCode === 27) {
        // on escape
        if (this.filteredItems.length > 0) {
          this.showDropDown = false
          e.preventDefault()
        }
      }
    },
    onDoubleClick () {
      this.searchTerm = ''
      this.showDropDown = true
    },
    onBlur () {
      setTimeout(() => {
        this.showDropDown = false
      }, 200)
    },
    selectItem (item) {
      if (item === null || item === undefined || item.name === null || item.name === undefined || item.name === '') {
        return
      }

      for (let i = 0; i < this.filteredItems.length; i++) {
        if (this.filteredItems[i].name === item.name) {
          this.selectionIndex = i
          break
        }
      }

      let start = this.getSelectionStart()
      let end = this.getSelectionEnd()
      const text = this.$refs.editor.quill.getText()
      if (start === end) {
        // there is no selection
        const term = this.getSearchTermFromString(text)
        start -= term.length

        const right = this.getWordRightFromCaret(text)
        end += right.length
      } else {
        // there is something selected
        const charsBeforeSelection = this.value.substring(start - this.prefix.length, start)
        if (charsBeforeSelection === this.prefix) {
          start -= this.prefix.length
        }
        const charsAfterSelection = this.value.substring(end, end + this.postfix.length)
        if (charsAfterSelection === this.postfix) {
          end += this.postfix.length
        }
      }
      this.$refs.editor.quill.updateContents(
        new Delta().retain(start).delete(end - start).insert(this.prefix + item.name + this.postfix)
      )
      this.$refs.editor.quill.setSelection(start + item.name.length + 2)
      this.showDropDown = false
      this.$emit('input', this.$refs.editor.quill.root.innerHTML)
      this.$root.$nextTick(() => {
        this.focusInput()
      })
    },
    focusInput () {
      this.$refs.editor.quill.focus()
    },
    increaseSelectionIndex () {
      if (this.selectionIndex >= this.filteredItems.length - 1) {
        this.selectionIndex = 0
      } else {
        this.selectionIndex += 1
      }
    },
    decreaseSelectionIndex () {
      if (this.selectionIndex <= 0) {
        this.selectionIndex = this.filteredItems.length - 1
      } else {
        this.selectionIndex -= 1
      }
    },
    onResize () {
      this.updateMinWidthProperty()
    },
    updateMinWidthProperty () {
      if (this.$refs.editor) {
        this.width = this.$refs.editor.quill.root.clientWidth
      }
    }
  }
}
</script>

<style scoped>
.editor {
  border: 1px solid var(--v-dfltBackground-darken1) !important;
  white-space: pre;
}
.selected {
  background-color: cornsilk;
}
.template-field {
  width: 100%;
  position: relative;
  display: inline-block;
  background-color: white;
}
.types {
  display: inline-block;
  position: fixed;
  margin-top: -40px;
  max-height: 500px;
  padding: 5px 0;
  box-shadow: 0 1px 5px 1px rgba(0,0,0,0.3);
  overflow-y: auto;
  overflow-x: hidden;
  contain: content;
  z-index: 99;
}
.list {
  width: 100%;
  height: 100%;
  font-size: 1.1em;
  overflow-x: hidden;
  padding: 0;
}
.list span {
  font-family: "Roboto", sans-serif;
  font-size: 0.9em;
  padding-left: 10px;
  color: #787878;
}
</style>
