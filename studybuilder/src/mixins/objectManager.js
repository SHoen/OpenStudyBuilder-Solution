import { bus } from '@/main'
import instances from '@/utils/instances'

export const objectManagerMixin = {
  methods: {
    async setParameterValues (data, parameters) {
      data.parameterValues = await instances.formatParameterValues(parameters)
    },
    getInitialFormContent () {
      return {
        library: {
          name: 'Sponsor'
        }
      }
    },
    close () {
      this.form = this.getInitialFormContent()
      this.parameters = []
      this.$refs.observer.reset()
      this.$emit('close')
    },
    showParametersFromTemplate (template, useDefaultValues) {
      this.apiTemplateEndpoint.getObjectTemplateParameters(template.uid).then(resp => {
        this.parameterResponse = resp.data
        const parameters = []
        resp.data.forEach(value => {
          if (value.format) {
            parameters.push(...value.parameters)
          } else {
            parameters.push(value)
          }
        })
        if (useDefaultValues && template.defaultParameterValues) {
          instances.loadParameterValues(template.defaultParameterValues, parameters, true)
        }
        this.parameters = parameters
      })
    },
    getSeparator (conjunction) {
      if (conjunction === ',') {
        return ', '
      } else {
        return ' ' + conjunction + ' '
      }
    },
    showParametersFromObject (object) {
      this.apiEndpoint.getObjectParameters(object.uid).then(resp => {
        this.parameterResponse = resp.data

        const parameters = []
        resp.data.forEach(value => {
          if (value.format) {
            parameters.push(...value.parameters)
          } else {
            parameters.push(value)
          }
        })
        this.parameters = parameters
        this.apiEndpoint.getObject(object.uid).then(resp => {
          instances.loadParameterValues(resp.data.parameterValues, this.parameters)
        })
      })
    },
    async addObject () {
      const data = JSON.parse(JSON.stringify(this.form))

      data[this.objectTemplateUidLabel] = data[this.objectTemplateUidResultLabel].uid
      delete data[this.objectTemplateUidResultLabel]
      data.libraryName = data.library.name
      delete data.library
      await this.setParameterValues(data, this.parameters)

      return this.$store.dispatch(this.storeEndpointAdd, data).then(resp => {
        bus.$emit('notification', { msg: this.$t(this.translationLabel + '.add_success') })
      })
    },
    async updateObject () {
      const data = JSON.parse(JSON.stringify(this.form))
      data.parameterUids = []
      await this.setParameterValues(data, this.parameters)
      return this.$store.dispatch(this.storeEndpointUpdate, { uid: this.objectUid, data }).then(resp => {
        bus.$emit('notification', { msg: this.$t(this.translationLabel + '.update_success') })
      })
    }
  }
}
