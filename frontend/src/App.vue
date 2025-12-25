<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import router from "./router";

onMounted(() => {
  // Default to project list
  if (router.currentRoute.value.path === "/") {
    router.push("/projects");
  }
});
</script>

<style scoped>
#app {
  min-height: 100vh;
}
</style>

