<script setup>
import { ref, computed, onMounted } from 'vue'
import { reportsApi } from '../api/client'
import { krw, firstDayOfYear, today } from '../utils/format'
import LineChart from '../components/charts/LineChart.vue'

const date_from = ref(firstDayOfYear())
const date_to = ref(today())
const data = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try { data.value = await reportsApi.cashFlow({ date_from: date_from.value, date_to: date_to.value }) }
  finally { loading.value = false }
}

onMounted(load)

const chart = computed(() => {
  const rows = data.value?.rows ?? []
  return {
    labels: rows.map((r) => r.month),
    datasets: [
      { label: '유입', data: rows.map((r) => Number(r.inflow)), borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.15)', tension: 0.3, fill: true },
      { label: '유출', data: rows.map((r) => Number(r.outflow)), borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.15)', tension: 0.3, fill: true },
      { label: '순현금흐름', data: rows.map((r) => Number(r.net)), borderColor: '#2563eb', tension: 0.3 },
    ],
  }
})
</script>

<template>
  <div class="space-y-6">
    <div class="card flex flex-wrap items-end gap-3">
      <div><label class="label">시작일</label><input type="date" v-model="date_from" class="input" /></div>
      <div><label class="label">종료일</label><input type="date" v-model="date_to" class="input" /></div>
      <button class="btn-primary" @click="load" :disabled="loading">{{ loading ? '조회 중...' : '조회' }}</button>
    </div>

    <div v-if="data" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="card">
          <div class="text-sm text-slate-500">총 유입</div>
          <div class="text-2xl font-bold text-emerald-600 mt-1">{{ krw(data.total_inflow) }}</div>
        </div>
        <div class="card">
          <div class="text-sm text-slate-500">총 유출</div>
          <div class="text-2xl font-bold text-red-600 mt-1">{{ krw(data.total_outflow) }}</div>
        </div>
        <div class="card">
          <div class="text-sm text-slate-500">순현금흐름</div>
          <div class="text-2xl font-bold mt-1" :class="Number(data.net) >= 0 ? 'text-brand-600' : 'text-red-600'">
            {{ krw(data.net) }}
          </div>
        </div>
      </div>

      <div class="card">
        <div class="text-base font-semibold mb-3">월별 현금흐름</div>
        <LineChart v-if="data.rows.length" :data="chart" />
        <div v-else class="text-center text-slate-400 py-10">데이터가 없습니다</div>
      </div>

      <div class="card">
        <div class="text-base font-semibold mb-3">월별 상세</div>
        <table class="table">
          <thead>
            <tr><th>월</th><th class="text-right">유입</th><th class="text-right">유출</th><th class="text-right">순흐름</th></tr>
          </thead>
          <tbody>
            <tr v-for="r in data.rows" :key="r.month">
              <td>{{ r.month }}</td>
              <td class="text-right text-emerald-600">{{ krw(r.inflow) }}</td>
              <td class="text-right text-red-600">{{ krw(r.outflow) }}</td>
              <td class="text-right font-medium" :class="Number(r.net) >= 0 ? 'text-brand-600' : 'text-red-600'">
                {{ krw(r.net) }}
              </td>
            </tr>
            <tr v-if="!data.rows.length">
              <td colspan="4" class="text-center text-slate-400 py-6">데이터가 없습니다</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
