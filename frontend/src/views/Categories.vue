<script setup>
import { ref, onMounted } from 'vue'
import { categoriesApi } from '../api/client'

const items = ref([])
const form = ref({ name: '', type: 'EXPENSE' })
const error = ref('')

async function load() {
  items.value = await categoriesApi.list()
}

async function save() {
  error.value = ''
  try {
    await categoriesApi.create({ name: form.value.name.trim(), type: form.value.type })
    form.value.name = ''
    await load()
  } catch (e) { error.value = e.message }
}

async function remove(id) {
  if (!confirm('삭제하시겠습니까? 관련 거래의 카테고리가 미분류로 변경될 수 있습니다.')) return
  try {
    await categoriesApi.remove(id)
    await load()
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="card">
      <div class="section-title mb-3">카테고리 추가</div>
      <div class="flex gap-2">
        <select v-model="form.type" class="input max-w-[120px]">
          <option value="INCOME">수입</option>
          <option value="EXPENSE">지출</option>
        </select>
        <input v-model="form.name" class="input flex-1" placeholder="카테고리 이름" @keyup.enter="save" />
        <button class="btn-primary" @click="save">추가</button>
      </div>
      <div v-if="error" class="text-red-600 text-sm mt-2">{{ error }}</div>
    </div>

    <div class="card">
      <div class="section-title mb-3">카테고리 목록</div>
      <table class="table">
        <thead>
          <tr><th>구분</th><th>이름</th><th class="w-24"></th></tr>
        </thead>
        <tbody>
          <tr v-for="c in items" :key="c.id">
            <td>
              <span :class="c.type === 'INCOME' ? 'badge-income' : 'badge-expense'">
                {{ c.type === 'INCOME' ? '수입' : '지출' }}
              </span>
            </td>
            <td>{{ c.name }}</td>
            <td class="text-right"><button class="btn-danger" @click="remove(c.id)">삭제</button></td>
          </tr>
          <tr v-if="!items.length">
            <td colspan="3" class="text-center text-slate-400 py-6">등록된 카테고리가 없습니다</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
