<template>
  <nav aria-label="Panel samping" class="hidden md:flex flex-col items-center gap-2 py-2 w-14 shrink-0 rounded-2xl border border-bontang-line bg-bontang-panel">
    <button
      type="button"
      class="relative p-2.5 rounded-xl hover:bg-bontang-raised"
      :class="open ? 'bg-bontang-raised text-bontang-accent' : 'text-bontang-muted hover:text-bontang-text'"
      :aria-expanded="open"
      aria-controls="panel-kanan"
      :aria-label="open ? 'Sembunyikan informasi objek dan legenda' : 'Tampilkan informasi objek dan legenda'"
      :title="open ? 'Sembunyikan informasi dan legenda' : 'Informasi objek dan legenda'"
      @click="$emit('toggle')"
    >
      <UiIcon name="info" />
      <span v-if="hasSelection" class="absolute right-1.5 top-1.5 w-2 h-2 rounded-full bg-bontang-accent" aria-hidden="true"></span>
    </button>
  </nav>
</template>

<script setup>
import UiIcon from '@/components/ui/UiIcon.vue';

defineProps({ open: { type: Boolean, required: true }, hasSelection: { type: Boolean, default: false } });
defineEmits(['toggle']);
</script>
