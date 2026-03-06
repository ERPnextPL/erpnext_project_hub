<script setup>
import { RouterView } from "vue-router";
import OfflineBanner from "./components/OfflineBanner.vue";
import UpdateBanner from "./components/UpdateBanner.vue";
</script>

<template>
	<UpdateBanner />
	<OfflineBanner />
	<RouterView />
</template>
