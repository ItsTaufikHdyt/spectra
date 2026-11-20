<template>
  <div class="space-y-2">
    <div
      role="group"
      aria-label="Mode tampilan"
      class="grid grid-cols-3 gap-1 p-1 rounded-lg bg-bontang-ink border border-bontang-line"
    >
      <button
        v-for="(m, id) in settings.modes"
        :key="id"
        type="button"
        :aria-pressed="settings.level === id"
        class="px-2 py-1.5 rounded-md font-medium"
        :class="
          settings.level === id
            ? 'bg-bontang-raised text-bontang-text ring-1 ring-inset ring-bontang-accent'
            : 'text-bontang-muted hover:text-bontang-text'
        "
        @click="settings.setLevel(id)"
      >
        {{ m.label }}
      </button>
    </div>
    <p class="text-small text-bontang-muted">{{ settings.modes[settings.level].note }}</p>

    <div
      v-if="settings.autoNotice"
      role="status"
      class="flex items-start justify-between gap-2 rounded-lg border border-bontang-accent/60 p-2.5 text-small"
    >
      <p class="break-words">{{ settings.autoNotice }}</p>
      <button
        type="button"
        class="shrink-0 p-1 rounded-md text-bontang-muted hover:text-bontang-text hover:bg-bontang-raised"
        aria-label="Tutup pemberitahuan"
        @click="settings.dismissNotice()"
      >
        <svg viewBox="0 0 20 20" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.75" aria-hidden="true">
          <path d="M5 5l10 10M15 5L5 15" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { useSettingsStore } from '@/stores/settingsStore';

const settings = useSettingsStore();
</script>
