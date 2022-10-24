import Vue from 'vue'
import Vuetify from 'vuetify/lib'
import { Resize, Ripple, Scroll } from 'vuetify/lib/directives'

Vue.use(Vuetify, {
  directives: {
    Resize,
    Ripple,
    Scroll
  }
})

export default new Vuetify({
  theme: {
    options: {
      customProperties: true
    },
    themes: {
      light: {
        primary: '#193074',
        secondary: '#0a56c2',
        accent: '#2196f3',
        error: '#f44336',
        warning: '#EAAB00',
        info: '#0a56c2',
        success: '#4caf50',
        green: '#3f9c35',
        red: '#e6553f',
        orange: '#FF9800',
        dfltBackground: '#f2f7fd',
        dfltBackgroundLight1: '#B1D5F2',
        dfltBackgroundLight2: '#D8EAF8',
        greyBackground: '#ebe8e5',
        nnLightBlue1: '#334784',
        nnLightBlue2: '#6675a3',
        nnLightBlue4: '#e5e8ef',
        nnDarkBlue1: '#2267c8',
        nnGreen1: '#2a918b',
        nnPink1: '#eea7bf',
        parameterBackground: '#E0E0E0'
      },
      dark: {
        primary: '#ff9800',
        secondary: '#cddc39',
        accent: '#2196f3',
        error: '#f44336',
        warning: '#795548',
        info: '#607d8b',
        success: '#4caf50'
      }
    }
  }
})
