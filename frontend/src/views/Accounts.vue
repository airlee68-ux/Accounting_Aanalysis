<script setup>
import { ref, onMounted } from 'vue'
import { accountsApi } from '../api/client'

const items = ref([])
const form = ref({ code: '', name: '', type: 'ASSET', description: '' })
const error = ref('')

const TYPE_LABEL = {
  ASSET: '자산', LIABILITY: '부채', EQUITY: '자본', REVENUE: '수익', EXPENSE: '비용',
}

async function load() {
  items.value = await accountsApi.list()
}

async function save() {
  error.value = ''
  try {
    await accountsApi.create({ ...form.value, code: form.value.code.trim(), name: form.value.name.trim() })
    form.value = { code: '', name: '', type: 'ASSET', description: '' }
    await load()
  } catch (e) { error.value = e.message }
}

async function remove(id) {
  if (!confirm('삭제하시겠습니까?')) return
  try { await accountsApi.remove(id); await load() } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="card">
      <div class="section-title mb-3">계정과목 추가</div>
      <div class="grid grid-cols-1 md:grid-cols-6 gap-2">
        <input v-model="form.code" class="input" placeholder="코드 (예: 1010)" />
        <input v-model="form.name" class="input md:col-span-2" placeholder="계정명 (예: 현금)" />
        <select v-model="form.type" class="input">
          <option value="ASSET">자산</option>
          <option value="LIABILITY">부채</option>
          <option value="EQUITY">자본</option>
          <option value="REVENUE">수익</option>
          <option value="EXPENSE">비용</option>
        </select>
        <input v-model="form.description" class="input" placeholder="설명 (선택)" />
        <button class="btn-primary" @click="save">추가</button>
      </div>
      <div v-if="error" class="text-red-600 text-sm mt-2">{{ error }}</div>
    </div>

    <div class="card">
      <div class="section-title mb-3">계정과목 목록</div>
      <table class="table">
        <thead>
          <tr><th>코드</th><th>계정명</th><th>유형</th><th>설명</th><th class="w-24"></th></tr>
        </thead>
        <tbody>
          <tr v-for="a in items" :key="a.id">
            <td class="font-mono num">{{ a.code }}</td>
            <td>{{ a.name }}</td>
            <td>{{ TYPE_LABEL[a.type] }}</td>
            <td class="muted">{{ a.description || '-' }}</td>
            <td class="text-right"><button class="btn-danger" @click="remove(a.id)">삭제</button></td>
          </tr>
          <tr v-if="!items.length">
            <td colspan="5" class="text-center text-slate-400 py-6">등록된 계정과목이 없습니다</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
