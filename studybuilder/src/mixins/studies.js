import { mapGetters } from 'vuex'
import store from '@/store'

export const studySelectedNavigationGuard = {

  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    studyId () {
      return (this.selectedStudy.studyNumber !== undefined && this.selectedStudy.studyNumber !== null)
        ? this.selectedStudy.studyId : this.selectedStudy.studyAcronym
    }
  },

  /*
  ** Check if target route requires a selected study or not.
  */
  async beforeRouteEnter (to, from, next) {
    if (to.meta && to.meta.studyRequired && !store.state.studiesGeneral.selectedStudy) {
      next(false)
    } else {
      next()
    }
  }
}
