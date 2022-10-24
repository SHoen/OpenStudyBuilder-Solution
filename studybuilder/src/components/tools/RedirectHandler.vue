<template>
<div>
  <confirm-dialog ref="confirm" :text-cols="5" :action-cols="6">
    <template v-slot:actions>
      <v-btn
        color="white"
        @click.native="openSelectStudyDialog"
        outlined
        class="mr-2"
        elevation="2"
        >
        {{ $t('_global.select_study') }}
      </v-btn>
      <v-btn
        color="white"
        @click.native="redirectToStudyTable"
        outlined
        elevation="2"
        >
        {{ $t('_global.add_study') }}
      </v-btn>
    </template>
  </confirm-dialog>
  <v-dialog
    v-model="showSelectForm"
    persistent
    max-width="600px"
    >
    <study-quick-select-form @close="showSelectForm = false" @selected="goToNextUrl" />
  </v-dialog>
</div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import StudyQuickSelectForm from '@/components/studies/StudyQuickSelectForm'

export default {
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  components: {
    ConfirmDialog,
    StudyQuickSelectForm
  },
  props: {
    target: Object
  },
  mounted () {
    this.items = this.studies
  },
  data () {
    return {
      items: [],
      expanded: false,
      showSelectForm: false,
      nextUrl: null
    }
  },
  methods: {
    ...mapActions({
      addBreadcrumbsLevel: 'app/addBreadcrumbsLevel'
    }),
    startFrom (arr, idx) {
      return arr.slice(idx)
    },
    async redirect (target) {
      if (target.subitem && target.subitem.studyRequired && !this.selectedStudy) {
        const options = {
          type: 'warning'
        }
        this.nextUrl = target.subitem.url
        await this.$refs.confirm.open(this.$t('_global.no_study_selected'), options)
      } else {
        target.subitem ? this.$router.push(target.subitem.url) : this.$router.push(target.item.url)
      }
      if (Object.prototype.hasOwnProperty.call(target.item, 'meta')) {
        const breads = target.item.meta.breadcrumb
        this.addBreadcrumbsLevel({
          text: breads[0].name
        })
        this.addBreadcrumbsLevel({
          text: breads[1].name
        })
      } else {
        this.addBreadcrumbsLevel({ text: target.item.title, to: target.item.url, index: 1 })
        if (target.subitem !== undefined) {
          this.addBreadcrumbsLevel({ text: target.subitem.title, to: target.subitem.url })
        }
      }
    },
    openSelectStudyDialog () {
      this.$refs.confirm.cancel()
      this.showSelectForm = true
    },
    redirectToStudyTable () {
      this.$refs.confirm.cancel()
      this.$router.push({ name: 'SelectOrAddStudy' })
    },
    goToNextUrl () {
      this.$router.push(this.nextUrl)
      this.nextUrl = null
    }
  },
  watch: {
    target (value) {
      this.redirect(value)
    }
  }
}
</script>
