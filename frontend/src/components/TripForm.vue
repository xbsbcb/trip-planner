<script setup>
import { reactive } from "vue"

const emit = defineEmits(["submit"])
const form = reactive({
  city: "北京",
  start_date: "2025-06-01",
  end_date: "2025-06-03",
  travel_days: 3,
  transportation: "公共交通",
  accommodation: "经济型酒店",
  preferences: ["历史文化", "美食"],
  free_text_input: "",
})

const prefOptions = ["历史文化", "自然风光", "美食", "都市观光", "购物", "亲子", "博物馆", "夜景"]

function togglePref(p) {
  const i = form.preferences.indexOf(p)
  i >= 0 ? form.preferences.splice(i, 1) : form.preferences.push(p)
}

function submit() {
  emit("submit", { ...form, travel_days: Number(form.travel_days) })
}
</script>

<template>
  <form @submit.prevent="submit" class="trip-form">
    <div class="form-row">
      <label>目的地</label>
      <input v-model="form.city" required />
    </div>
    <div class="form-row">
      <label>开始日期</label>
      <input type="date" v-model="form.start_date" required />
    </div>
    <div class="form-row">
      <label>结束日期</label>
      <input type="date" v-model="form.end_date" required />
    </div>
    <div class="form-row">
      <label>旅行天数</label>
      <input type="number" v-model="form.travel_days" min="1" max="30" required />
    </div>
    <div class="form-row">
      <label>交通方式</label>
      <select v-model="form.transportation">
        <option>公共交通</option>
        <option>自驾</option>
        <option>打车+地铁</option>
      </select>
    </div>
    <div class="form-row">
      <label>住宿偏好</label>
      <select v-model="form.accommodation">
        <option>经济型酒店</option>
        <option>舒适型酒店</option>
        <option>豪华型酒店</option>
        <option>民宿</option>
      </select>
    </div>
    <div class="form-row">
      <label>偏好标签</label>
      <div class="pref-tags">
        <button
          v-for="p in prefOptions"
          :key="p"
          type="button"
          :class="{ active: form.preferences.includes(p) }"
          @click="togglePref(p)"
        >
          {{ p }}
        </button>
      </div>
    </div>
    <div class="form-row">
      <label>额外要求</label>
      <textarea v-model="form.free_text_input" placeholder="希望多安排一些博物馆..." rows="2" />
    </div>
    <button type="submit" class="btn-submit">开始规划</button>
  </form>
</template>

<style scoped>
.trip-form { max-width: 480px; margin: 0 auto; }
.form-row { margin-bottom: 16px; }
.form-row label { display: block; margin-bottom: 4px; font-weight: 600; }
.form-row input, .form-row select, .form-row textarea {
  width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px;
  font-size: 14px;
}
.pref-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.pref-tags button {
  padding: 4px 12px; border: 1px solid #ccc; border-radius: 16px;
  background: #fff; cursor: pointer; font-size: 13px;
}
.pref-tags button.active { background: #4f46e5; color: #fff; border-color: #4f46e5; }
.btn-submit {
  width: 100%; padding: 12px; background: #4f46e5; color: #fff;
  border: none; border-radius: 8px; font-size: 16px; cursor: pointer;
}
.btn-submit:hover { background: #4338ca; }
</style>
