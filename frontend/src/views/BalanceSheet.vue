<script setup>
import { ref, onMounted, computed } from 'vue'
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

function group(rows, cls) {
  return (rows || []).filter(r => r.classification === cls)
}

const currentAssets   = computed(() => group(data.value?.assets, 'current'))
const ncAssets        = computed(() => group(data.value?.assets, 'non_current'))
const currentLiab     = computed(() => group(data.value?.liabilities, 'current'))
const ncLiab          = computed(() => group(data.value?.liabilities, 'non_current'))
const paidIn          = computed(() => group(data.value?.equity, 'paid_in'))
const retained        = computed(() => group(data.value?.equity, 'retained'))
const oci             = computed(() => group(data.value?.equity, 'oci'))
</script>

<template>
  <div class="space-y-6">
    <div class="card flex flex-wrap items-end gap-3">
      <div><label class="label">기준일</label><input type="date" v-model="as_of" class="input" /></div>
      <button class="btn-primary" @click="load" :disabled="loading">{{ loading ? '조회 중...' : '조회' }}</button>
      <div class="ml-auto text-xs text-slate-500">K-IFRS 유동성 구분</div>
    </div>

    <div v-if="data" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 자산 -->
      <div class="card">
        <div class="section-title mb-3 text-brand-700">자산 (Assets)</div>

        <div class="mb-2 text-xs font-semibold text-slate-500 uppercase">유동자산</div>
        <table class="table">
          <tbody>
            <tr v-for="(r, i) in currentAssets" :key="'ca'+i">
              <td>{{ r.account }}</td>
              <td class="text-right font-medium num">{{ krw(r.balance) }}</td>
            </tr>
            <tr v-if="!currentAssets.length"><td colspan="2" class="text-center text-slate-400 py-2">-</td></tr>
          </tbody>
          <tfoot>
            <tr class="bg-brand-50/60">
              <td class="font-semibold">유동자산 합계</td>
              <td class="text-right font-bold text-brand-700 num">{{ krw(data.current_assets) }}</td>
            </tr>
          </tfoot>
        </table>

        <div class="mt-5 mb-2 text-xs font-semibold text-slate-500 uppercase">비유동자산</div>
        <table class="table">
          <tbody>
            <tr v-for="(r, i) in ncAssets" :key="'nca'+i">
              <td>{{ r.account }}</td>
              <td class="text-right font-medium num">{{ krw(r.balance) }}</td>
            </tr>
            <tr v-if="!ncAssets.length"><td colspan="2" class="text-center text-slate-400 py-2">-</td></tr>
          </tbody>
          <tfoot>
            <tr class="bg-brand-50/60">
              <td class="font-semibold">비유동자산 합계</td>
              <td class="text-right font-bold text-brand-700 num">{{ krw(data.non_current_assets) }}</td>
            </tr>
            <tr class="bg-brand-50">
              <td class="font-semibold">자산 총계</td>
              <td class="text-right font-bold text-brand-700 num">{{ krw(data.total_assets) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- 부채·자본 -->
      <div class="card space-y-6">
        <div>
          <div class="section-title mb-3 text-amber-700">부채 (Liabilities)</div>

          <div class="mb-2 text-xs font-semibold text-slate-500 uppercase">유동부채</div>
          <table class="table">
            <tbody>
              <tr v-for="(r, i) in currentLiab" :key="'cl'+i">
                <td>{{ r.account }}</td>
                <td class="text-right font-medium num">{{ krw(r.balance) }}</td>
              </tr>
              <tr v-if="!currentLiab.length"><td colspan="2" class="text-center text-slate-400 py-2">-</td></tr>
            </tbody>
            <tfoot>
              <tr class="bg-amber-50/60">
                <td class="font-semibold">유동부채 합계</td>
                <td class="text-right font-bold text-amber-700 num">{{ krw(data.current_liabilities) }}</td>
              </tr>
            </tfoot>
          </table>

          <div class="mt-5 mb-2 text-xs font-semibold text-slate-500 uppercase">비유동부채</div>
          <table class="table">
            <tbody>
              <tr v-for="(r, i) in ncLiab" :key="'ncl'+i">
                <td>{{ r.account }}</td>
                <td class="text-right font-medium num">{{ krw(r.balance) }}</td>
              </tr>
              <tr v-if="!ncLiab.length"><td colspan="2" class="text-center text-slate-400 py-2">-</td></tr>
            </tbody>
            <tfoot>
              <tr class="bg-amber-50/60">
                <td class="font-semibold">비유동부채 합계</td>
                <td class="text-right font-bold text-amber-700 num">{{ krw(data.non_current_liabilities) }}</td>
              </tr>
              <tr class="bg-amber-50">
                <td class="font-semibold">부채 총계</td>
                <td class="text-right font-bold text-amber-700 num">{{ krw(data.total_liabilities) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div>
          <div class="section-title mb-3 text-indigo-700">자본 (Equity)</div>
          <table class="table">
            <tbody>
              <template v-if="paidIn.length">
                <tr><td colspan="2" class="text-xs font-semibold text-slate-500 uppercase pt-2">납입자본</td></tr>
                <tr v-for="(r, i) in paidIn" :key="'pi'+i">
                  <td>{{ r.account }}</td>
                  <td class="text-right font-medium num">{{ krw(r.balance) }}</td>
                </tr>
              </template>
              <template v-if="retained.length">
                <tr><td colspan="2" class="text-xs font-semibold text-slate-500 uppercase pt-2">이익잉여금</td></tr>
                <tr v-for="(r, i) in retained" :key="'re'+i">
                  <td>{{ r.account }}</td>
                  <td class="text-right font-medium num">{{ krw(r.balance) }}</td>
                </tr>
              </template>
              <template v-if="oci.length">
                <tr><td colspan="2" class="text-xs font-semibold text-slate-500 uppercase pt-2">기타자본</td></tr>
                <tr v-for="(r, i) in oci" :key="'oci'+i">
                  <td>{{ r.account }}</td>
                  <td class="text-right font-medium num">{{ krw(r.balance) }}</td>
                </tr>
              </template>
              <tr v-if="!data.equity.length"><td colspan="2" class="text-center text-slate-400 py-4">-</td></tr>
            </tbody>
            <tfoot>
              <tr class="bg-indigo-50">
                <td class="font-semibold">자본 총계</td>
                <td class="text-right font-bold text-indigo-700 num">{{ krw(data.total_equity) }}</td>
              </tr>
              <tr class="bg-slate-100">
                <td class="font-semibold">부채 + 자본</td>
                <td class="text-right font-bold num">
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
