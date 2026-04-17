<script setup>
import { ref, onMounted } from 'vue'
import { reportsApi } from '../api/client'
import { krw, today } from '../utils/format'

const as_of = ref(today())
const data = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try { data.value = await reportsApi.balanceSheet({ as_of: as_of.value }) }
  finally { loading.value = false }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="card flex flex-wrap items-end gap-3">
      <div><label class="label">기준일</label><input type="date" v-model="as_of" class="input" /></div>
      <button class="btn-primary" @click="load" :disabled="loading">{{ loading ? '조회 중...' : '조회' }}</button>
    </div>

    <div v-if="data" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <div class="text-base font-semibold mb-3 text-brand-700">자산 (Assets)</div>
        <table class="table">
          <thead><tr><th>계정</th><th class="text-right">잔액</th></tr></thead>
          <tbody>
            <tr v-for="(r, i) in data.assets" :key="'a'+i">
              <td>{{ r.account }}</td>
              <td class="text-right font-medium">{{ krw(r.balance) }}</td>
            </tr>
            <tr v-if="!data.assets.length"><td colspan="2" class="text-center text-slate-400 py-4">-</td></tr>
          </tbody>
          <tfoot>
            <tr class="bg-brand-50">
              <td class="font-semibold">자산 총계</td>
              <td class="text-right font-bold text-brand-700">{{ krw(data.total_assets) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div class="card space-y-5">
        <div>
          <div class="text-base font-semibold mb-3 text-amber-700">부채 (Liabilities)</div>
          <table class="table">
            <thead><tr><th>계정</th><th class="text-right">잔액</th></tr></thead>
            <tbody>
              <tr v-for="(r, i) in data.liabilities" :key="'l'+i">
                <td>{{ r.account }}</td>
                <td class="text-right font-medium">{{ krw(r.balance) }}</td>
              </tr>
              <tr v-if="!data.liabilities.length"><td colspan="2" class="text-center text-slate-400 py-4">-</td></tr>
            </tbody>
            <tfoot>
              <tr class="bg-amber-50">
                <td class="font-semibold">부채 총계</td>
                <td class="text-right font-bold text-amber-700">{{ krw(data.total_liabilities) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div>
          <div class="text-base font-semibold mb-3 text-indigo-700">자본 (Equity)</div>
          <table class="table">
            <thead><tr><th>계정</th><th class="text-right">잔액</th></tr></thead>
            <tbody>
              <tr v-for="(r, i) in data.equity" :key="'e'+i">
                <td>{{ r.account }}</td>
                <td class="text-right font-medium">{{ krw(r.balance) }}</td>
              </tr>
              <tr v-if="!data.equity.length"><td colspan="2" class="text-center text-slate-400 py-4">-</td></tr>
            </tbody>
            <tfoot>
              <tr class="bg-indigo-50">
                <td class="font-semibold">자본 총계</td>
                <td class="text-right font-bold text-indigo-700">{{ krw(data.total_equity) }}</td>
              </tr>
              <tr class="bg-slate-100">
                <td class="font-semibold">부채 + 자본</td>
                <td class="text-right font-bold">
                  {{ krw(Number(data.total_liabilities) + Number(data.total_equity)) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
