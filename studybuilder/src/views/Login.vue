<template>
<div></div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  computed: {
    ...mapGetters({
      userInfo: 'auth/userInfo'
    })
  },
  mounted () {
    if (this.userInfo) {
      this.$router.push({ name: 'Studies' })
    }
  }
}
</script>
