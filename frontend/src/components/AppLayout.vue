<script setup>
import { RouterLink, useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()

const nav = [
  { to: '/', label: '대시보드', icon: '📊' },
  { to: '/transactions', label: '거래내역', icon: '💳' },
  { to: '/categories', label: '카테고리', icon: '🏷️' },
  { to: '/accounts', label: '계정과목', icon: '📒' },
]
const reports = [
  { to: '/reports/income-statement', label: '손익계산서' },
  { to: '/reports/balance-sheet', label: '대차대조표' },
  { to: '/reports/cash-flow', label: '현금흐름표' },
]

const currentTitle = computed(() => route.meta?.title || 'Accounting')
</script>

<template>
  <div class="min-h-screen flex">
    <aside class="w-60 bg-white border-r border-slate-200 flex flex-col">
      <div class="px-5 py-4 border-b border-slate-200">
        <div class="text-lg font-bold text-brand-700">Accounting</div>
        <div class="text-xs text-slate-500">회계 분석 시스템</div>
      </div>
      <nav class="flex-1 p-3 space-y-1">
        <RouterLink v-for="item in nav" :key="item.to" :to="item.to"
          class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-slate-100"
          active-class="bg-brand-50 text-brand-700 font-medium">
          <span>{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>

        <div class="pt-4 pb-1 px-3 text-xs font-semibold text-slate-400 uppercase">재무제표</div>
        <RouterLink v-for="item in reports" :key="item.to" :to="item.to"
          class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm hover:bg-slate-100"
          active-class="bg-brand-50 text-brand-700 font-medium">
          <span>📑</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="p-3 text-xs text-slate-400 border-t border-slate-200">
        FastAPI + Vue 3
      </div>
    </aside>

    <main class="flex-1 flex flex-col">
      <header class="bg-white border-b border-slate-200 px-6 py-3">
        <h1 class="text-lg font-semibold text-slate-800">{{ currentTitle }}</h1>
      </header>
      <div class="flex-1 p-6 overflow-auto">
        <slot />
      </div>
    </main>
  </div>
</template>
