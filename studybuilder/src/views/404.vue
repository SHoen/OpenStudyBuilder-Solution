<template>
  <div class="mt-6 text-center">
    <h1>{{ $t('404View.title') }}</h1>
    <v-btn class="mt-4" color="primary" @click="navigateToRoot" text>{{ $t('404View.back_home') }}</v-btn>
  </div>
</template>

<script>
export default {
  mounted () {
    this.$store.commit('app/RESET_BREADCRUMBS')
  },
  methods: {
    navigateToRoot () {
      this.$store.commit('app/SET_SECTION', '')
      this.$router.push('/')
    }
  }
}
</script>
