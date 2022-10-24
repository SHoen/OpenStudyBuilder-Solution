<template>
  <div class="mt-6 text-center">
    <h1>{{ $t('UnderConstruction.title') }}</h1>
    <v-btn class="mt-4" color="primary" @click="navigateToRoot" text>{{ $t('UnderConstruction.back_home') }}</v-btn>
  </div>
</template>

<script>
export default {
  methods: {
    navigateToRoot () {
      this.$store.commit('app/SET_SECTION', '')
      this.$router.push('/')
    }
  }
}
</script>
