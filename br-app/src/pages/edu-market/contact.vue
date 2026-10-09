<template>
  <web-view :src="knocketUrl" />
</template>

<script>
export default {
  data() {
    return {
      knocketUrl: '',
    }
  },
  onLoad(options) {
    this.knocketUrl =
      options.url ||
      'https://trtc.io/knocket-sdk/sdk.js?identifier=0ee9b993c7ff89bb61&v=1791511906929'
  },
}
</script>
