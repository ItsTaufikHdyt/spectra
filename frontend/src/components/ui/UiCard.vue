<template>
  <section class="rounded-2xl border border-bontang-line bg-bontang-panel" :aria-labelledby="id">
    <h2 class="m-0">
      <button
        v-if="collapsible"
        :id="id"
        type="button"
        class="w-full flex items-center justify-between gap-2 px-4 py-3 rounded-2xl text-left text-body font-semibold"
        :aria-expanded="open"
        :aria-controls="`${id}-isi`"
        @click="open = !open"
      >
        {{ title }}
        <UiIcon name="chevron" class="text-bontang-muted motion-safe:transition-transform" :class="open ? '' : 'rotate-180'" />
      </button>
      <span v-else :id="id" class="block px-4 pt-3 text-body font-semibold">{{ title }}</span>
    </h2>
    <div v-show="open" :id="`${id}-isi`" class="px-4 pb-4" :class="collapsible ? '' : 'pt-2'">
      <slot />
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue';
import UiIcon from '@/components/ui/UiIcon.vue';

const props = defineProps({
  title: { type: String, required: true },
  collapsible: { type: Boolean, default: false },
  startOpen: { type: Boolean, default: true }
});
const open = ref(props.collapsible ? props.startOpen : true);
// id tetap per instans agar aria-labelledby/aria-controls valid
const id = `kartu-${Math.random().toString(36).slice(2, 8)}`;
</script>
