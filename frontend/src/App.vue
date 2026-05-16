<script setup>
import { ref } from "vue"
import TripForm from "./components/TripForm.vue"
import AgentProgress from "./components/AgentProgress.vue"
import PlanResult from "./components/PlanResult.vue"
import MapView from "./components/MapView.vue"
import { useTripStream } from "./composables/useTripStream.js"

const { events, plan, error, running, currentLabel, start } = useTripStream()
const tab = ref("plan")

function onSubmit(request) {
  start(request)
}
</script>

<template>
  <div class="app-shell">
    <header>
      <h1>Trip Planner</h1>
      <span class="subtitle">多智能体旅行规划</span>
    </header>

    <main>
      <TripForm @submit="onSubmit" :disabled="running" />

      <div v-if="running || events.length" class="progress-section">
        <AgentProgress :events="events" :current-label="currentLabel" />
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <div v-if="plan" class="result-section">
        <div class="tabs">
          <button :class="{ active: tab === 'plan' }" @click="tab = 'plan'">行程计划</button>
          <button :class="{ active: tab === 'map' }" @click="tab = 'map'">地图视图</button>
        </div>

        <PlanResult v-if="tab === 'plan'" :plan="plan" />
        <MapView v-if="tab === 'map'" :plan="plan" />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-shell { max-width: 720px; margin: 0 auto; padding: 24px 16px; }
header { text-align: center; margin-bottom: 32px; }
header h1 { margin: 0; font-size: 28px; }
.subtitle { color: #94a3b8; font-size: 14px; }
.progress-section { margin: 24px 0; }
.result-section { margin-top: 32px; }
.tabs { display: flex; gap: 8px; margin-bottom: 16px; }
.tabs button {
  flex: 1; padding: 10px; border: 1px solid #e2e8f0; border-radius: 8px;
  background: #fff; cursor: pointer; font-size: 14px;
}
.tabs button.active { background: #4f46e5; color: #fff; border-color: #4f46e5; }
.error {
  margin-top: 16px; padding: 12px; background: #fef2f2; color: #dc2626;
  border-radius: 8px; font-size: 14px;
}
</style>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; background: #f8fafc; }
</style>
