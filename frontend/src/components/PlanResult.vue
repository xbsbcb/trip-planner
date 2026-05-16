<script setup>
defineProps({ plan: Object })
</script>

<template>
  <div class="plan" v-if="plan">
    <div class="plan-header">
      <h2>{{ plan.city }}</h2>
      <span class="dates">{{ plan.start_date }} — {{ plan.end_date }}</span>
    </div>

    <div class="day-card" v-for="day in plan.days" :key="day.day_index">
      <h3>第{{ day.day_index + 1 }}天 · {{ day.date }}</h3>
      <p class="day-desc">{{ day.description }}</p>

      <div class="day-meta">
        <span>🚗 {{ day.transportation }}</span>
        <span>🏨 {{ day.accommodation }}</span>
      </div>

      <div class="hotel-card" v-if="day.hotel">
        <strong>推荐酒店: {{ day.hotel.name }}</strong>
        <span class="hotel-meta">
          ⭐{{ day.hotel.rating }} | {{ day.hotel.price_range }} | {{ day.hotel.distance }}
        </span>
        <p class="hotel-addr">{{ day.hotel.address }}</p>
      </div>

      <div class="attractions">
        <h4>景点</h4>
        <div class="attraction-item" v-for="attr in day.attractions" :key="attr.name">
          <div class="attr-main">
            <strong>{{ attr.name }}</strong>
            <span class="attr-cat">{{ attr.category }}</span>
          </div>
          <p class="attr-desc">{{ attr.description }}</p>
          <div class="attr-meta">
            <span>⏱ {{ attr.visit_duration }}分钟</span>
            <span v-if="attr.ticket_price">🎫 ¥{{ attr.ticket_price }}</span>
            <span v-else>🎫 免费</span>
          </div>
        </div>
      </div>

      <div class="meals">
        <h4>餐饮</h4>
        <div class="meal-item" v-for="meal in day.meals" :key="meal.type">
          <strong>{{ { breakfast: "早餐", lunch: "午餐", dinner: "晚餐" }[meal.type] }}</strong>
          <span>{{ meal.name }}</span>
          <span class="meal-desc" v-if="meal.description">— {{ meal.description }}</span>
          <span class="meal-cost">¥{{ meal.estimated_cost }}</span>
        </div>
      </div>
    </div>

    <div class="weather" v-if="plan.weather_info?.length">
      <h3>天气预报</h3>
      <div class="weather-item" v-for="w in plan.weather_info" :key="w.date">
        <strong>{{ w.date }}</strong>
        <span>☀️{{ w.day_temp }}°C</span>
        <span>🌙{{ w.night_temp }}°C</span>
        <span>{{ w.day_weather }}</span>
        <span>🌬{{ w.wind_direction }}{{ w.wind_power }}</span>
      </div>
    </div>

    <div class="budget" v-if="plan.budget">
      <h3>预算汇总</h3>
      <div class="budget-grid">
        <div>景点门票 <span>¥{{ plan.budget.total_attractions }}</span></div>
        <div>酒店住宿 <span>¥{{ plan.budget.total_hotels }}</span></div>
        <div>餐饮费用 <span>¥{{ plan.budget.total_meals }}</span></div>
        <div>交通出行 <span>¥{{ plan.budget.total_transportation }}</span></div>
        <div class="total">总计 <span>¥{{ plan.budget.total }}</span></div>
      </div>
    </div>

    <div class="suggestions" v-if="plan.overall_suggestions">
      <h3>旅行建议</h3>
      <p>{{ plan.overall_suggestions }}</p>
    </div>
  </div>
</template>

<style scoped>
.plan { max-width: 640px; margin: 0 auto; }
.plan-header { text-align: center; margin-bottom: 24px; }
.plan-header h2 { margin: 0; font-size: 28px; }
.dates { color: #64748b; }
.day-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 20px; margin-bottom: 16px;
}
.day-card h3 { margin: 0 0 8px; }
.day-desc { color: #475569; margin: 0 0 12px; }
.day-meta { display: flex; gap: 16px; font-size: 13px; color: #94a3b8; margin-bottom: 12px; }
.hotel-card {
  background: #f0f9ff; border-radius: 8px; padding: 12px; margin-bottom: 16px;
}
.hotel-meta { display: block; font-size: 13px; color: #64748b; margin-top: 4px; }
.hotel-addr { font-size: 12px; color: #94a3b8; margin: 4px 0 0; }
.attractions h4, .meals h4 { margin: 12px 0 8px; color: #334155; }
.attraction-item {
  border-left: 3px solid #4f46e5; padding: 8px 12px; margin-bottom: 8px;
}
.attr-main { display: flex; align-items: center; gap: 8px; }
.attr-cat { font-size: 12px; background: #eef2ff; color: #4f46e5; padding: 2px 8px; border-radius: 8px; }
.attr-desc { font-size: 13px; color: #64748b; margin: 4px 0; }
.attr-meta { font-size: 12px; color: #94a3b8; display: flex; gap: 12px; }
.meal-item { display: flex; align-items: center; gap: 8px; font-size: 13px; padding: 4px 0; }
.meal-desc { color: #94a3b8; font-size: 12px; }
.meal-cost { margin-left: auto; color: #4f46e5; font-weight: 600; }
.weather { margin: 20px 0; }
.weather-item { display: flex; gap: 12px; font-size: 13px; padding: 6px 0; }
.budget { margin: 20px 0; }
.budget-grid div {
  display: flex; justify-content: space-between; padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
}
.budget-grid .total { font-weight: 700; border: none; }
.suggestions { background: #fffbeb; border-radius: 10px; padding: 16px; margin-top: 20px; }
.suggestions p { font-size: 14px; color: #78350f; line-height: 1.6; }
</style>
