<script setup>
import { ref, onMounted } from 'vue'
import { reportsApi } from '../api/client'
import { krw, firstDayOfYear, today } from '../utils/format'

const date_from = ref(firstDayOfYear())
const date_to = ref(today())
const data = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try { data.value = await reportsApi.incomeStatement({ date_from: date_from.value, date_to: date_to.value }) }
  finally { loading.value = false }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="card flex flex-wrap items-end gap-3">
      <div><label class="label">시작일</label><input type="date" v-model="date_from" class="input" /></div>
      <div><label class="label">종료일</label><input type="date" v-model="date_to" class="input" /></div>
      <button class="btn-primary" @click="load" :disabled="loading">{{ loading ? '조회 중...' : '조회' }}</button>
    </div>

    <div v-if="data" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <div class="text-base font-semibold mb-3 text-emerald-700">수익 (Revenue)</div>
        <table class="table">
          <thead><tr><th>계정</th><th class="text-right">금액</th></tr></thead>
          <tbody>
            <tr v-for="r in data.revenue" :key="r.category">
              <td>{{ r.category }}</td>
              <td class="text-right font-medium">{{ krw(r.amount) }}</td>
            </tr>
            <tr v-if="!data.revenue.length"><td colspan="2" class="text-center text-slate-400 py-4">-</td></tr>
          </tbody>
          <tfoot>
            <tr class="bg-emerald-50">
              <td class="font-semibold">수익 합계</td>
              <td class="text-right font-bold text-emerald-700">{{ krw(data.total_revenue) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div class="card">
        <div class="text-base font-semibold mb-3 text-red-700">비용 (Expense)</div>
        <table class="table">
          <thead><tr><th>계정</th><th class="text-right">금액</th></tr></thead>
          <tbody>
            <tr v-for="r in data.expense" :key="r.category">
              <td>{{ r.category }}</td>
              <td class="text-right font-medium">{{ krw(r.amount) }}</td>
            </tr>
            <tr v-if="!data.expense.length"><td colspan="2" class="text-center text-slate-400 py-4">-</td></tr>
          </tbody>
          <tfoot>
            <tr class="bg-red-50">
              <td class="font-semibold">비용 합계</td>
              <td class="text-right font-bold text-red-700">{{ krw(data.total_expense) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div class="card lg:col-span-2">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-slate-500">{{ data.period_start }} ~ {{ data.period_end }}</div>
            <div class="text-lg font-semibold">당기순이익 (Net Income)</div>
          </div>
          <div class="text-3xl font-bold" :class="Number(data.net_income) >= 0 ? 'text-brand-600' : 'text-red-600'">
            {{ krw(data.net_income) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
