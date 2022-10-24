import Vue from 'vue'
import { DateTime } from 'luxon'
import i18n from './plugins/i18n'

/*
** Return a human readable version of the given date string.
*/
Vue.filter('date', function (value) {
  return DateTime.fromISO(value).setLocale('en').toLocaleString(DateTime.DATETIME_MED)
})

/*
** Display a boolean value as a yes/no alternative.
*/
Vue.filter('yesno', function (value) {
  if (value === undefined || value === null) {
    return ''
  }
  return (value) ? i18n.t('_global.yes') : i18n.t('_global.no')
})

/*
** Remove square brackets from the given value.
*/
Vue.filter('stripBrackets', function (value) {
  return value.replaceAll(/\[|\]/g, '')
})

/*
** Display a list of terms
*/
Vue.filter('terms', function (value) {
  if (!value) {
    return ''
  }
  return value.map(item => item.name.sponsorPreferredName).join(', ')
})

/*
** Display a list of objects names
*/
Vue.filter('names', function (value) {
  if (!value) {
    return ''
  }
  return value.map(item => item.name).join(', ')
})

/*
** Display a list of lag times
*/
Vue.filter('lagTimes', function (value) {
  return value.map(item => `${item.sdtmDomainLabel}: ${item.value} ${item.unitLabel}`).join(', ')
})

/*
** Display a list of substances
*/
Vue.filter('substances', function (value) {
  return value.map(item => `${item.substanceName} (${item.substanceUnii})`).join(', ')
})

/*
** Display a list of pharmacological classes
*/
Vue.filter('pharmacologicalClasses', function (value) {
  return value.map(item => (item !== null && item.pclassName) ? `${item.pclassName} (${item.pclassId})` : null).filter(pclass => pclass !== null).join(', ')
})
