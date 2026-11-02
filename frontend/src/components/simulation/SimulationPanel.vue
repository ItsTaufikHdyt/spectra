<template>
  <section aria-labelledby="judul-simulasi" class="space-y-2">
    <h2 id="judul-simulasi" class="text-small font-semibold text-bontang-muted">Simulasi</h2>

    <ul class="rounded-lg border border-bontang-line divide-y divide-bontang-line">
      <!-- Simulasi terdaftar (registry) -->
      <li v-for="sim in SIMULATIONS" :key="sim.id" class="p-3 space-y-2">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="font-medium">{{ sim.name }}</p>
            <p class="text-small text-bontang-muted">{{ sim.description }}</p>
          </div>
          <button
            v-if="store.activeId !== sim.id"
            type="button"
            class="shrink-0 px-2.5 py-1 rounded-md border border-bontang-edge text-small font-medium hover:bg-bontang-raised"
            @click="activate(sim.id)"
          >
            Jalankan
          </button>
          <button
            v-else
            type="button"
            class="shrink-0 px-2.5 py-1 rounded-md bg-bontang-accent text-bontang-accent-ink text-small font-semibold"
            @click="deactivate()"
          >
            Hentikan
          </button>
        </div>

        <template v-if="store.activeId === sim.id">
          <p v-if="store.status === 'loading'" class="text-small text-bontang-muted" role="status">Menyiapkan simulasi…</p>
          <p v-else-if="store.status === 'error'" class="text-small text-bontang-danger" role="alert">
            Simulasi gagal: {{ store.error }}
          </p>
          <component
            :is="sim.ParameterPanel"
            :params="store.params"
            :disabled="store.status !== 'active'"
            @update:params="updateParams"
          />
        </template>
      </li>

      <!-- Direncanakan -->
      <li v-for="item in PLANNED_SIMULATIONS" :key="item.id" class="flex items-start justify-between gap-3 p-3">
        <div>
          <p class="font-medium text-bontang-muted">{{ item.name }}</p>
          <p class="text-small text-bontang-subtle">{{ item.note }}</p>
        </div>
        <span class="shrink-0 px-2 py-0.5 rounded-full border border-bontang-line text-caption text-bontang-muted">Segera hadir</span>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { SIMULATIONS, PLANNED_SIMULATIONS } from '@/simulations';
import { useSimulationStore } from '@/stores/simulationStore';
import { useSimulation } from '@/composables/useSimulation';

const store = useSimulationStore();
const { activate, deactivate, updateParams } = useSimulation();
</script>
