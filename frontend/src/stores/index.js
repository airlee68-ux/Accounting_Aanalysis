import { defineStore } from 'pinia'
import { categoriesApi, accountsApi } from '../api/client'

export const useMetaStore = defineStore('meta', {
  state: () => ({
    categories: [],
    accounts: [],
    loading: false,
  }),
  actions: {
    async loadCategories(force = false) {
      if (!force && this.categories.length) return this.categories
      this.categories = await categoriesApi.list()
      return this.categories
    },
    async loadAccounts(force = false) {
      if (!force && this.accounts.length) return this.accounts
      this.accounts = await accountsApi.list()
      return this.accounts
    },
  },
  getters: {
    incomeCategories: (s) => s.categories.filter((c) => c.type === 'INCOME'),
    expenseCategories: (s) => s.categories.filter((c) => c.type === 'EXPENSE'),
  },
})
