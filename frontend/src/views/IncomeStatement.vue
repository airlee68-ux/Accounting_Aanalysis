<script setup>
import { ref, onMounted, computed } from 'vue'
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

const opMargin = computed(() => {
  if (!data.value || Number(data.value.sales) === 0) return 0
  return (Number(data.value.operating_profit) / Number(data.value.sales)) * 100
})
const grossMargin = computed(() => {
  if (!data.value || Number(data.value.sales) === 0) return 0
  return (Number(data.value.gross_profit) / Number(data.value.sales)) * 100
})
</script>

<template>
  <div class="space-y-6">
    <div class="card flex flex-wrap items-end gap-3">
      <div><label class="label">시작일</label><input type="date" v-model="date_from" class="input" /></div>
      <div><label class="label">종료일</label><input type="date" v-model="date_to" class="input" /></div>
      <button class="btn-primary" @click="load" :disabled="loading">{{ loading ? '조회 중...' : '조회' }}</button>
      <div class="ml-auto text-xs text-slate-500">K-IFRS 기능별 표시</div>
    </div>

    <div v-if="data" class="space-y-6">
      <!-- IFRS 단계별 손익 요약 -->
      <div class="card">
        <div class="section-title mb-4">단계별 손익 (IFRS)</div>
        <div class="space-y-1 text-sm">
          <div class="flex justify-between py-2">
            <span>매출액</span>
            <span class="num font-medium">{{ krw(data.sales) }}</span>
          </div>
          <div class="flex justify-between py-2 text-slate-600">
            <span>(-) 매출원가</span>
            <span class="num">{{ krw(data.cogs) }}</span>
          </div>
          <div class="flex justify-between py-2 border-t font-semibold bg-emerald-50 px-2 rounded">
            <span>매출총이익 <span class="text-xs text-slate-500">({{ grossMargin.toFixed(1) }}%)</span></span>
            <span class="num text-emerald-700">{{ krw(data.gross_profit) }}</span>
          </div>
          <div class="flex justify-between py-2 text-slate-600">
            <span>(-) 판매비와관리비</span>
            <span class="num">{{ krw(data.sga) }}</span>
          </div>
          <div class="flex justify-between py-2 border-t font-semibold bg-brand-50 px-2 rounded">
            <span>영업이익 <span class="text-xs text-slate-500">({{ opMargin.toFixed(1) }}%)</span></span>
            <span class="num text-brand-700">{{ krw(data.operating_profit) }}</span>
          </div>
          <div class="flex justify-between py-2 text-slate-600">
            <span>(+) 기타수익(영업외)</span>
            <span class="num">{{ krw(data.other_income) }}</span>
          </div>
          <div class="flex justify-between py-2 text-slate-600">
            <span>(-) 금융원가</span>
            <span class="num">{{ krw(data.finance_cost) }}</span>
          </div>
          <div class="flex justify-between py-2 border-t font-semibold">
            <span>법인세비용차감전순이익</span>
            <span class="num">{{ krw(data.profit_before_tax) }}</span>
          </div>
          <div class="flex justify-between py-2 text-slate-600">
            <span>(-) 법인세비용</span>
            <span class="num">{{ krw(data.income_tax) }}</span>
          </div>
          <div class="flex justify-between py-3 border-t-2 font-bold text-lg" :class="Number(data.net_income) >= 0 ? 'text-brand-700' : 'text-red-700'">
            <span>당기순이익</span>
            <span class="num">{{ krw(data.net_income) }}</span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="card">
          <div class="section-title mb-3 text-emerald-700">수익 (Revenue) — 카테고리별</div>
          <table class="table">
            <thead><tr><th>계정</th><th class="text-right">금액</th></tr></thead>
            <tbody>
              <tr v-for="r in data.revenue" :key="r.category">
                <td>{{ r.category }}</td>
                <td class="text-right font-medium num">{{ krw(r.amount) }}</td>
              </tr>
              <tr v-if="!data.revenue.length"><td colspan="2" class="text-center text-slate-400 py-4">-</td></tr>
            </tbody>
            <tfoot>
              <tr class="bg-emerald-50">
                <td class="font-semibold">수익 합계</td>
                <td class="text-right font-bold text-emerald-700 num">{{ krw(data.total_revenue) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div class="card">
          <div class="section-title mb-3 text-red-700">비용 (Expense) — 카테고리별</div>
          <table class="table">
            <thead><tr><th>계정</th><th class="text-right">금액</th></tr></thead>
            <tbody>
              <tr v-for="r in data.expense" :key="r.category">
                <td>{{ r.category }}</td>
                <td class="text-right font-medium num">{{ krw(r.amount) }}</td>
              </tr>
              <tr v-if="!data.expense.length"><td colspan="2" class="text-center text-slate-400 py-4">-</td></tr>
            </tbody>
            <tfoot>
              <tr class="bg-red-50">
                <td class="font-semibold">비용 합계</td>
                <td class="text-right font-bold text-red-700 num">{{ krw(data.total_expense) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
