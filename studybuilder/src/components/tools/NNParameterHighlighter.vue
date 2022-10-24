<template>
<div class="template-readonly"
     v-html="getFormatedParts()"
     >
</div>
</template>

<script>
export default {
  props: {
    value: Array,
    // the name including the parameters
    name: {
      type: String,
      default: ''
    },
    prefix: {
      type: String,
      default: '['
    },
    postfix: {
      type: String,
      default: ']'
    },
    showPrefixAndPostfix: {
      type: Boolean,
      default: true
    },
    parameters: {
      type: Array,
      default: () => []
    },
    editionMode: {
      type: Boolean,
      default: false
    },
    defaultColor: {
      type: String,
      default: 'green'
    },
    defaultParameterValues: {
      type: Array,
      required: false
    }
  },
  data: () => ({
    selectedParams: null
  }),
  computed: {
    computedPostfix () {
      return this.postfix === '' || this.postfix === null || this.postfix === undefined ? ' ' : this.postfix
    },
    nameParts () {
      const nameArray = []
      let parameterIndex = 0

      let chars = ''
      for (const char of this.name) {
        if (char === this.prefix) {
          nameArray.push({
            isParameter: false,
            value: chars
          })
          if (this.showPrefixAndPostfix) {
            chars = char
          } else {
            chars = ''
          }
        } else if (char === this.computedPostfix) {
          let fromDefaultValue = false
          if (this.showPrefixAndPostfix) {
            chars += char
          }
          if (this.defaultParameterValues && this.defaultParameterValues.length) {
            for (const parameter of this.defaultParameterValues) {
              if (parameterIndex + 1 === parameter.position && parameter.values.length) {
                const values = parameter.values.map(value => value.name)
                chars = `${this.prefix}${values.join(parameter.conjunction)}${this.computedPostfix}`
                fromDefaultValue = true
                break
              }
            }
          }
          nameArray.push({
            isParameter: true,
            index: parameterIndex,
            value: chars,
            fromDefaultValue
          })
          parameterIndex++
          chars = ''
        } else {
          chars += char
        }
      }
      nameArray.push({
        isParameter: false,
        value: chars
      })
      return nameArray
    }
  },
  methods: {
    getNamePartClass (namePart) {
      if (!namePart.isParameter) {
        return 'preview-text black--text'
      }
      if (this.editionMode && this.parameters[namePart.index]) {
        if (!this.parameters.length || !this.parameters[namePart.index].selectedValues || !this.parameters[namePart.index].selectedValues.length) {
          return 'preview-parameter'
        }
        return 'preview-parameter--selected'
      }
      if (!namePart.fromDefaultValue) {
        return `parameter--${this.defaultColor}`
      }
      return 'preview-parameter--selected'
    },
    getFormatedParts () {
      let result = ''
      this.nameParts.forEach((namePart, index) => {
        if (namePart.isParameter) {
          result += `<span class="${this.getNamePartClass(namePart, index)}">${namePart.value}</span>`
        } else {
          result += namePart.value
        }
      })
      return result
    }
  }
}
</script>

<style lang="scss">
.template-readonly {
  min-height: 30px;

  p {
    margin-bottom: 4px;
  }
}
.preview-parameter {
  color: var(--v-orange-base);

  &--selected {
    color: var(--v-green-base);
  }
}
.parameter {
  &--orange {
    color: var(--v-orange-base);
  }
  &--green {
    color: var(--v-green-base);
  }
  &--primary {
    color: var(--v-primary-base);
  }
}
.param-dropdown {
  width: 160px;
  display: inline-block;
}
</style>
