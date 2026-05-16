<script setup>
import { ref, onMounted, watch } from "vue"

const props = defineProps({ plan: Object, amapKey: String })
const mapContainer = ref(null)
const mapReady = ref(false)

let map = null
let markers = []

function loadAmap() {
  return new Promise((resolve) => {
    const key = props.amapKey || "509c9939093b18967fa744b5d0ea16e3"
    const script = document.createElement("script")
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${key}`
    script.onload = resolve
    document.head.appendChild(script)
  })
}

function clearMarkers() {
  markers.forEach(m => m.setMap(null))
  markers = []
}

function addMarkers(plan) {
  const points = []

  for (const day of plan.days || []) {
    for (const attr of day.attractions || []) {
      if (attr.location?.longitude && attr.location?.latitude) {
        points.push({
          lnglat: [attr.location.longitude, attr.location.latitude],
          name: attr.name,
          type: "attraction",
        })
      }
    }
    if (day.hotel?.location?.longitude && day.hotel?.location?.latitude) {
      points.push({
        lnglat: [day.hotel.location.longitude, day.hotel.location.latitude],
        name: day.hotel.name,
        type: "hotel",
      })
    }
  }

  points.forEach((p) => {
    const marker = new window.AMap.Marker({
      position: p.lnglat,
      title: p.name,
      icon: p.type === "hotel"
        ? "https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png"
        : "https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png",
    })
    marker.setMap(map)
    markers.push(marker)
  })

  if (points.length) {
    map.setFitView(markers)
  }
}

onMounted(async () => {
  await loadAmap()
  map = new window.AMap.Map(mapContainer.value, { zoom: 13 })
  mapReady.value = true
  if (props.plan) addMarkers(props.plan)
})

watch(() => props.plan, (p) => {
  if (p && map) addMarkers(p)
})
</script>

<template>
  <div class="map-wrap">
    <div ref="mapContainer" class="map-container" />
    <div class="map-legend">
      <span><span class="dot blue" /> 景点</span>
      <span><span class="dot red" /> 酒店</span>
    </div>
  </div>
</template>

<style scoped>
.map-wrap { position: relative; }
.map-container { width: 100%; height: 420px; border-radius: 12px; overflow: hidden; }
.map-legend {
  position: absolute; bottom: 10px; left: 10px;
  background: rgba(255,255,255,0.9); padding: 6px 12px;
  border-radius: 8px; display: flex; gap: 16px; font-size: 12px;
}
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; }
.blue { background: #6495ed; }
.red { background: #e74c3c; }
</style>
