import Vue from 'vue'
import { ValidationObserver, ValidationProvider, extend } from 'vee-validate'
import { max, max_value, min_value, numeric, required } from 'vee-validate/dist/rules' // eslint-disable-line camelcase
import i18n from './i18n'

// Declare builtin rules here
extend('numeric', {
  ...numeric,
  message: () => i18n.t('_errors.numeric')
})
extend('required', {
  ...required,
  message: () => i18n.t('_errors.required')
})
extend('max', {
  ...max,
  message: i18n.t('_errors.max_length_reached')
})
extend('max_value', {
  ...max_value, // eslint-disable-line camelcase
  message: i18n.t('_errors.max_value_reached')
})
extend('min_value', {
  ...min_value, // eslint-disable-line camelcase
  message: i18n.t('_errors.min_value_reached')
})

// Add custom rules here
extend('requiredIfNotNA', {
  params: ['target'],
  validate: (value, { target }) => {
    let valueIsSet = value !== undefined && value !== null
    if (valueIsSet && typeof value === 'object') {
      if (Object.keys(value).length === 0) {
        valueIsSet = false
      }
    }
    return (valueIsSet || target === 'true' || target === true)
  },
  message: i18n.t('_errors.required'),
  computesRequired: true
})

extend('oneselected', {
  validate: (value, [target]) => {
    const valueIsUnset = value === undefined || value === null || Object.keys(value).length === 0
    const targetIsUnset = target === undefined || target === null || Object.keys(target).length === 0
    return !(!valueIsUnset && !targetIsUnset)
  },
  message: i18n.t('_errors.exclusive_select')
}, {
  hasTarget: true
})

extend('atleastone', {
  validate: (value, [target]) => {
    const valueIsUnset = value === undefined || value === null || Object.keys(value).length === 0
    const targetIsUnset = target === undefined || target === null || Object.keys(target).length === 0
    return !(valueIsUnset && targetIsUnset)
  },
  message: i18n.t('_errors.select_at_least_one')
}, {
  hasTarget: true
})

extend('age', {
  validate: (value) => {
    return (!value.ageNumericValue && !value.ageUnitCode) ||
      (value.ageNumericValue !== undefined && value.ageUnitCode !== undefined)
  },
  message: i18n.t('_errors.duration_incomplete')
})

extend('duration', {
  validate: (value) => {
    return (!value.numericValue && !value.unitCode) ||
      (value.numericValue !== undefined && value.unitCode !== undefined)
  },
  message: i18n.t('_errors.duration_incomplete')
})

// Register components globally
Vue.component('ValidationObserver', ValidationObserver)
Vue.component('ValidationProvider', ValidationProvider)
