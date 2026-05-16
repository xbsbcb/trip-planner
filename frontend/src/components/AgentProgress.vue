<script setup>
defineProps({ events: Array, currentLabel: String })
</script>

<template>
  <div class="progress-panel" v-if="events.length">
    <h3>Agent 执行进度</h3>
    <div class="timeline">
      <div
        v-for="(e, i) in events"
        :key="i"
        class="timeline-item"
        :class="{ done: e.done, tool: e.node === 'tools_node' }"
      >
        <span class="dot" :class="{ done: e.done }" />
        <span class="label">{{ e.label }}</span>
        <span class="preview" v-if="e.preview">{{ e.preview.slice(0, 60) }}...</span>
      </div>
    </div>
    <div class="spinner" v-if="currentLabel && !events[events.length - 1]?.done">
      <span class="spin" /> {{ currentLabel }}
    </div>
  </div>
</template>

<style scoped>
.progress-panel {
  background: #f8fafc; border-radius: 10px; padding: 16px;
  max-width: 480px; margin: 0 auto;
}
h3 { margin: 0 0 12px; }
.timeline-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 0; font-size: 13px; color: #64748b;
}
.dot { width: 8px; height: 8px; border-radius: 50%; background: #cbd5e1; flex-shrink: 0; }
.dot.done { background: #22c55e; }
.label { font-weight: 500; white-space: nowrap; }
.preview { color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.spinner { display: flex; align-items: center; gap: 8px; margin-top: 8px; font-size: 13px; color: #4f46e5; }
.spin {
  width: 16px; height: 16px; border: 2px solid #e2e8f0;
  border-top-color: #4f46e5; border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
