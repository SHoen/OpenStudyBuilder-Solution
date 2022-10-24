import Vue from 'vue'
import { config } from '@vue/test-utils'
import Vuetify from 'vuetify'
import registerRequireContextHook from 'babel-plugin-require-context-hook/register'
import fetchMock from 'jest-fetch-mock'

config.mocks.$t = key => key
Vue.use(Vuetify)
Vue.config.productionTip = false
registerRequireContextHook()

process.env.BASE_URL = 'http://localhost:8080/'
fetchMock.mockResponse(
  JSON.stringify(
    {
      API_BASE_URL: 'http://127.0.0.1:8000',
      DOC_BASE_URL: 'http://127.0.0.1:8081',
      STUDYBUILDER_VERSION: 'v0.1',
      FRONTEND_BUILD_NUMBER: 'dev',
      API_BUILD_NUMBER: 'dev',
      DOCUMENTATION_PORTAL_BUILD_NUMBER: 'dev',
      AUTH_ENABLED: '0',
      AUTH_AUTHORITY: 'http://test.test',
      AUTH_APP_ID: 'test',
      AUTH_CLIENT_ID: 'test'
    }
  )
)
fetchMock.enableMocks()
