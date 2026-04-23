<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";

const props = defineProps({
  page: {
    type: String,
    required: true
  }
});

const router = useRouter();

const src = computed(() => `/legacy-static/${props.page}.html`);

function backHome() {
  router.push("/home");
}
</script>

<template>
  <div class="legacy-wrap">
    <iframe :src="src" title="legacy-page" />
  </div>
</template>

<style scoped>
.legacy-wrap {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
iframe {
  border: 0;
  flex: 1;
  width: 100%;
}
</style>
