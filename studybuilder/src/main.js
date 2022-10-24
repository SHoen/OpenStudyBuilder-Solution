import Vue from 'vue'
import './plugins/vee-validate'
import './filters'
import App from './App.vue'
import router from './router'
import store from './store'
import auth from './plugins/auth'
import vuetify from './plugins/vuetify'
import i18n from './plugins/i18n'
import sassStyles from './styles/global.scss' // eslint-disable-line no-unused-vars
import { ApplicationInsights, DistributedTracingModes } from '@microsoft/applicationinsights-web'
import '@/mixins/general'

Vue.config.productionTip = false

if (process.env.NODE_ENV !== 'development') {
  Vue.config.devtools = false
}

export const bus = new Vue()

fetch(process.env.BASE_URL + 'config.json').then(resp => {
  resp.json().then((config) => {
    Vue.prototype.$config = config
    Vue.use(auth)
    new Vue({
      router,
      store,
      vuetify,
      i18n,
      render: h => h(App)
    }).$mount('#app')
    const appInsights = new ApplicationInsights({
      config: {
        connectionString: Vue.prototype.$config.APPINSIGHTS_CONNSTRING,
        disableTelemetry: Vue.prototype.$config.APPINSIGHTS_DISABLE,
        enableAutoRouteTracking: true,
        enableAjaxErrorStatusText: true,
        autoTrackPageVisitTime: true,
        enableCorsCorrelation: true,
        enableRequestHeaderTracking: true,
        enableResponseHeaderTracking: true,
        distributedTracingMode: DistributedTracingModes.W3C
      }
    })
    appInsights.loadAppInsights()
    appInsights.trackPageView()
  })
})
