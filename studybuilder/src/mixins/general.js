import Vue from 'vue'

// Methods defined in this file are globally accessible

Vue.mixin({
  methods: {
    getHtmlLineBreaks (value) {
      return (value ? value.replaceAll('\n', '<br />') : '')
    }
  }
})
