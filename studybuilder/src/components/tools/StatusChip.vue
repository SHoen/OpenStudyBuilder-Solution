<template>
<v-chip :color="color" dark>{{ status }}</v-chip>
</template>

<script>
import statuses from '@/constants/statuses'

export default {
  props: ['status'],
  computed: {
    color () {
      if (this.status === statuses.FINAL) {
        return 'green'
      }
      if (this.status === statuses.RETIRED) {
        return 'orange'
      }
      return 'secondary'
    }
  }
}
</script>
