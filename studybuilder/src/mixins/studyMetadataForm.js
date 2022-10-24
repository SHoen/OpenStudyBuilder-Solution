export const studyMetadataFormMixin = {
  methods: {
    getTermPayload (name) {
      if (this.form[name]) {
        return {
          termUid: this.form[name].termUid,
          name: this.form[name].sponsorPreferredName || this.form[name].name
        }
      }
      return null
    },
    getTermsPayload (name) {
      const result = []
      if (!this.form[name]) {
        return null
      }
      this.form[name].forEach(term => {
        result.push({
          termUid: term.termUid,
          name: term.sponsorPreferredName || term.name
        })
      })
      return result
    }
  }
}
