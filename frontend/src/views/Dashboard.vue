<script setup>
import { ref, computed, onMounted } from 'vue'
import { reportsApi } from '../api/client'
import { krw, firstDayOfYear, today } from '../utils/format'
import BarChart from '../components/charts/BarChart.vue'
import DoughnutChart from '../components/charts/DoughnutChart.vue'

const dateFrom = ref(firstDayOfYear())
const dateTo = ref(today())
const data = ref(null)
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await reportsApi.dashboard({ date_from: dateFrom.value, date_to: dateTo.value })
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)

const monthlyChart = computed(() => {
  const rows = data.value?.monthly ?? []
  return {
    labels: rows.map((r) => r.month),
    datasets: [
      { label: '수입', data: rows.map((r) => Number(r.income)), backgroundColor: '#10b981' },
      { label: '지출', data: rows.map((r) => Number(r.expense)), backgroundColor: '#ef4444' },
    ],
  }
})

const expenseByCategory = computed(() => {
  const rows = (data.value?.by_category ?? []).filter((r) => r.type === 'EXPENSE')
  const palette = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#14b8a6', '#6366f1', '#84cc16']
  return {
    labels: rows.map((r) => r.category),
    datasets: [{ data: rows.map((r) => Number(r.amount)), backgroundColor: palette }],
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- 필터 -->
    <div class="card flex flex-wrap items-end gap-3">
      <div>
        <label class="label">시작일</label>
        <input type="date" v-model="dateFrom" class="input" />
      </div>
      <div>
        <label class="label">종료일</label>
        <input type="date" v-model="dateTo" class="input" />
      </div>
      <button class="btn-primary" @click="load" :disabled="loading">
        {{ loading ? '조회 중...' : '조회' }}
      </button>
      <div v-if="error" class="text-red-600 text-sm">{{ error }}</div>
    </div>

    <div v-if="data" class="space-y-6">
      <!-- KPI -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="card">
          <div class="text-sm muted">총 수입</div>
          <div class="text-2xl font-bold text-emerald-600 mt-1 num">{{ krw(data.total_income) }}</div>
        </div>
        <div class="card">
          <div class="text-sm muted">총 지출</div>
          <div class="text-2xl font-bold text-red-600 mt-1 num">{{ krw(data.total_expense) }}</div>
        </div>
        <div class="card">
          <div class="text-sm muted">순이익</div>
          <div class="text-2xl font-bold mt-1 num" :class="Number(data.net) >= 0 ? 'text-brand-600' : 'text-red-600'">
            {{ krw(data.net) }}
          </div>
        </div>
      </div>

      <!-- 차트 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="card lg:col-span-2">
          <div class="section-title mb-3">월별 수입·지출</div>
          <BarChart :data="monthlyChart" />
        </div>
        <div class="card">
          <div class="section-title mb-3">지출 카테고리 비중</div>
          <DoughnutChart v-if="expenseByCategory.labels.length" :data="expenseByCategory" />
          <div v-else class="text-sm text-slate-400 py-10 text-center">데이터가 없습니다</div>
        </div>
      </div>

      <!-- 최근 거래 -->
      <div class="card">
        <div class="section-title mb-3">최근 거래</div>
        <table class="table">
          <thead>
            <tr>
              <th>날짜</th><th>내용</th><th>카테고리</th><th>구분</th><th class="text-right">금액</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in data.recent_transactions" :key="t.id">
              <td>{{ t.date }}</td>
              <td>{{ t.description }}</td>
              <td>{{ t.category?.name || '-' }}</td>
              <td>
                <span :class="t.type === 'INCOME' ? 'badge-income' : 'badge-expense'">
                  {{ t.type === 'INCOME' ? '수입' : '지출' }}
                </span>
              </td>
              <td class="text-right font-medium num" :class="t.type === 'INCOME' ? 'text-emerald-600' : 'text-red-600'">
                {{ krw(t.amount) }}
              </td>
            </tr>
            <tr v-if="!data.recent_transactions.length">
              <td colspan="5" class="text-center text-slate-400 py-6">거래 내역이 없습니다</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
