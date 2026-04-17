<script setup>
import { ref, computed, onMounted } from 'vue'
import { transactionsApi } from '../api/client'
import { useMetaStore } from '../stores'
import { krw, today } from '../utils/format'

const meta = useMetaStore()
const items = ref([])
const loading = ref(false)
const error = ref('')

const filter = ref({ date_from: '', date_to: '', type: '', category_id: '' })

const form = ref(createEmpty())
const editingId = ref(null)

function createEmpty() {
  return { date: today(), description: '', amount: '', type: 'EXPENSE', category_id: '', memo: '' }
}

const categoriesForForm = computed(() =>
  meta.categories.filter((c) => !form.value.type || c.type === form.value.type),
)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const params = {}
    if (filter.value.date_from) params.date_from = filter.value.date_from
    if (filter.value.date_to) params.date_to = filter.value.date_to
    if (filter.value.type) params.type = filter.value.type
    if (filter.value.category_id) params.category_id = filter.value.category_id
    items.value = await transactionsApi.list(params)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function save() {
  error.value = ''
  try {
    const payload = {
      ...form.value,
      amount: Number(form.value.amount),
      category_id: form.value.category_id ? Number(form.value.category_id) : null,
    }
    if (editingId.value) {
      await transactionsApi.update(editingId.value, payload)
    } else {
      await transactionsApi.create(payload)
    }
    form.value = createEmpty()
    editingId.value = null
    await load()
  } catch (e) {
    error.value = e.message
  }
}

function edit(t) {
  editingId.value = t.id
  form.value = {
    date: t.date,
    description: t.description,
    amount: t.amount,
    type: t.type,
    category_id: t.category_id ?? '',
    memo: t.memo ?? '',
  }
}

function cancelEdit() {
  editingId.value = null
  form.value = createEmpty()
}

async function remove(id) {
  if (!confirm('삭제하시겠습니까?')) return
  await transactionsApi.remove(id)
  await load()
}

onMounted(async () => {
  await meta.loadCategories()
  await load()
})
</script>

<template>
  <div class="space-y-6">
    <!-- 입력 폼 -->
    <div class="card">
      <div class="text-base font-semibold mb-3">{{ editingId ? '거래 수정' : '거래 등록' }}</div>
      <div class="grid grid-cols-1 md:grid-cols-6 gap-3">
        <div>
          <label class="label">날짜</label>
          <input type="date" v-model="form.date" class="input" />
        </div>
        <div>
          <label class="label">구분</label>
          <select v-model="form.type" class="input">
            <option value="INCOME">수입</option>
            <option value="EXPENSE">지출</option>
          </select>
        </div>
        <div class="md:col-span-2">
          <label class="label">내용</label>
          <input v-model="form.description" class="input" placeholder="예: 4월 매출" />
        </div>
        <div>
          <label class="label">금액</label>
          <input type="number" v-model="form.amount" class="input" placeholder="0" />
        </div>
        <div>
          <label class="label">카테고리</label>
          <select v-model="form.category_id" class="input">
            <option value="">(선택)</option>
            <option v-for="c in categoriesForForm" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="md:col-span-5">
          <label class="label">메모</label>
          <input v-model="form.memo" class="input" />
        </div>
        <div class="flex items-end gap-2">
          <button class="btn-primary flex-1" @click="save">{{ editingId ? '수정' : '등록' }}</button>
          <button v-if="editingId" class="btn-secondary" @click="cancelEdit">취소</button>
        </div>
      </div>
      <div v-if="error" class="text-red-600 text-sm mt-2">{{ error }}</div>
    </div>

    <!-- 필터 -->
    <div class="card flex flex-wrap items-end gap-3">
      <div>
        <label class="label">시작일</label>
        <input type="date" v-model="filter.date_from" class="input" />
      </div>
      <div>
        <label class="label">종료일</label>
        <input type="date" v-model="filter.date_to" class="input" />
      </div>
      <div>
        <label class="label">구분</label>
        <select v-model="filter.type" class="input">
          <option value="">전체</option>
          <option value="INCOME">수입</option>
          <option value="EXPENSE">지출</option>
        </select>
      </div>
      <div>
        <label class="label">카테고리</label>
        <select v-model="filter.category_id" class="input">
          <option value="">전체</option>
          <option v-for="c in meta.categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <button class="btn-primary" @click="load" :disabled="loading">조회</button>
    </div>

    <!-- 목록 -->
    <div class="card">
      <div class="flex items-center justify-between mb-3">
        <div class="text-base font-semibold">거래 목록 ({{ items.length }})</div>
      </div>
      <div class="overflow-x-auto">
        <table class="table">
          <thead>
            <tr>
              <th>날짜</th><th>내용</th><th>카테고리</th><th>구분</th>
              <th class="text-right">금액</th><th>메모</th><th class="w-28"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in items" :key="t.id">
              <td>{{ t.date }}</td>
              <td>{{ t.description }}</td>
              <td>{{ t.category?.name || '-' }}</td>
              <td>
                <span :class="t.type === 'INCOME' ? 'badge-income' : 'badge-expense'">
                  {{ t.type === 'INCOME' ? '수입' : '지출' }}
                </span>
              </td>
              <td class="text-right font-medium" :class="t.type === 'INCOME' ? 'text-emerald-600' : 'text-red-600'">
                {{ krw(t.amount) }}
              </td>
              <td class="text-slate-500">{{ t.memo || '-' }}</td>
              <td class="text-right whitespace-nowrap">
                <button class="btn-secondary mr-1" @click="edit(t)">수정</button>
                <button class="btn-danger" @click="remove(t.id)">삭제</button>
              </td>
            </tr>
            <tr v-if="!items.length">
              <td colspan="7" class="text-center text-slate-400 py-6">거래 내역이 없습니다</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
