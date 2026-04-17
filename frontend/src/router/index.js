import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '대시보드' } },
  { path: '/transactions', name: 'transactions', component: () => import('../views/Transactions.vue'), meta: { title: '거래내역' } },
  { path: '/categories', name: 'categories', component: () => import('../views/Categories.vue'), meta: { title: '카테고리' } },
  { path: '/accounts', name: 'accounts', component: () => import('../views/Accounts.vue'), meta: { title: '계정과목' } },
  { path: '/reports/income-statement', name: 'income-statement', component: () => import('../views/IncomeStatement.vue'), meta: { title: '손익계산서' } },
  { path: '/reports/balance-sheet', name: 'balance-sheet', component: () => import('../views/BalanceSheet.vue'), meta: { title: '대차대조표' } },
  { path: '/reports/cash-flow', name: 'cash-flow', component: () => import('../views/CashFlow.vue'), meta: { title: '현금흐름표' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  if (to.meta?.title) document.title = `${to.meta.title} · Accounting`
})

export default router
