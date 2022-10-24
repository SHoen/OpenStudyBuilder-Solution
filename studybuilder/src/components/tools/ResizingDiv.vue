<template>
  <div v-resize="onResize">
    <div ref="resizingDiv">
      <slot name="resizing-area" :area-height="areaHeight" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'resizing-div',
  data () {
    return {
      areaHeight: 0
    }
  },
  props: {
    footerHeight: {
      type: Number,
      default: 115
    }
  },
  methods: {
    onResize () {
      this.areaHeight = this.getHeight()
    },
    getHeight () {
      const height = window.innerHeight -
      this.$refs.resizingDiv.getBoundingClientRect().y -
      this.footerHeight
      return height < 200 ? 400 : height
    }
  },
  updated () {
    const areaHeight = this.getHeight()
    if (areaHeight !== this.areaHeight) {
      this.areaHeight = areaHeight
    }
  }
}
</script>
