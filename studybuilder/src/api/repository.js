import Vue from 'vue'
import axios from 'axios'

import i18n from '@/plugins/i18n'
import { bus } from '@/main'

const _axios = axios.create()

_axios.interceptors.request.use(
  async function (config) {
    // Do something before request is sent
    config.baseURL = Vue.prototype.$config.API_BASE_URL

    // the component used to display available rows per page uses -1 to describe all elements
    // but API expects 0 to be sent to fetch all items in a paginated query
    if (config?.params?.pageSize === -1) {
      config.params.pageSize = 0
    }
    const accessToken = await Vue.prototype.$auth.getAccessToken()
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
      config.withCredentials = true
    } else {
      Vue.prototype.$auth.clear()
    }
    return config
  },
  function (error) {
    // Do something with request error
    return Promise.reject(error)
  }
)

// Add a response interceptor
_axios.interceptors.response.use(
  function (response) {
    // Just return unchanged response data
    return response
  },
  function (error) {
    const timeout = 30000
    if (!error.config.ignoreErrors) {
      if (!error.response) {
        // We do not have a response, we don't know the tracing id, just display the error.message
        bus.$emit('notification', {
          msg: error.message, type: 'error', timeout
        })
      } else if (error.response.status === 401) {
        // Unauthorized: handled elsewhere either by login-redirect or token-refresh routine
      } else {
        // If status code is 422, display the validation error details from error.response.data.detail.
        // Otherwise, just display the error message contained in error.response.data.message.

        let msg = (error.response.data && error.response.data.message) ? error.response.data.message : error.message
        let msgPrefix = ''

        if (error.response.status === 422) {
          // Validation error
          msgPrefix = i18n.t('_errors.validation_error')
          if (error.response.data && error.response.data.detail && Array.isArray(error.response.data.detail)) {
            // collect validation errors and include in error message
            const details = []
            error.response.data.detail.forEach(err => {
              if (err.loc && Array.isArray(err.loc)) {
                details.push(`"${err.loc.join('.')}" ${err.msg || err.type}`)
              }
            })
            if (details.length) {
              msg = details.join('; ') + '.'
            }
          }
        }

        bus.$emit('notification', {
          msg: `${msgPrefix} ${msg}`.trim(),
          type: 'error',
          timeout: timeout,
          correlationId: error.response.headers.traceresponse
        })
      }
    }
    return Promise.reject(error)
  }
)

export default _axios
