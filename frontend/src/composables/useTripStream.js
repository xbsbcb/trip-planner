import { ref } from "vue"
import { streamPlan } from "../api/trip.js"

export function useTripStream() {
  const events = ref([])
  const plan = ref(null)
  const error = ref(null)
  const running = ref(false)
  const currentLabel = ref("")

  async function start(request) {
    events.value = []
    plan.value = null
    error.value = null
    running.value = true

    try {
      for await (const event of streamPlan(request)) {
        events.value.push(event)
        currentLabel.value = event.label || ""
        if (event.done) {
          plan.value = event.plan
          break
        }
        if (event.error) {
          error.value = event.error
          break
        }
      }
    } catch (e) {
      error.value = e.message
    } finally {
      running.value = false
    }
  }

  return { events, plan, error, running, currentLabel, start }
}
