<script setup>
import { ref, computed, onMounted } from 'vue'
import { transactionsApi, importsApi } from '../api/client'
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

// --- 엑셀 임포트 ---
const fileInput = ref(null)
const importing = ref(false)
const importError = ref('')
const preview = ref(null) // { total, valid_count, error_count, rows }
const showPreview = ref(false)

function openFilePicker() {
  importError.value = ''
  fileInput.value?.click()
}

async function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  importing.value = true
  importError.value = ''
  try {
    const res = await importsApi.preview(file)
    preview.value = res
    showPreview.value = true
  } catch (err) {
    importError.value = err.message
  } finally {
    importing.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

function closePreview() {
  showPreview.value = false
  preview.value = null
}

async function confirmImport() {
  if (!preview.value) return
  const validRows = preview.value.rows
    .filter((r) => r.valid)
    .map((r) => ({
      date: r.date,
      type: r.type,
      description: r.description,
      amount: r.amount,
      category_id: r.category_id,
      memo: r.memo,
    }))
  if (!validRows.length) {
    importError.value = '저장할 유효한 행이 없습니다'
    return
  }
  importing.value = true
  importError.value = ''
  try {
    const res = await importsApi.confirm(validRows)
    closePreview()
    alert(`${res.inserted}건이 저장되었습니다`)
    await load()
  } catch (err) {
    importError.value = err.message
  } finally {
    importing.value = false
  }
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
      <div class="section-title mb-3">{{ editingId ? '거래 수정' : '거래 등록' }}</div>
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
      <div class="flex items-center justify-between mb-3 flex-wrap gap-2">
        <div class="section-title">거래 목록 ({{ items.length }})</div>
        <div class="flex items-center gap-2">
          <a :href="importsApi.templateUrl" class="btn-secondary" download>템플릿 다운로드</a>
          <button class="btn-primary" :disabled="importing" @click="openFilePicker">
            {{ importing ? '처리 중...' : '엑셀 업로드' }}
          </button>
          <input
            ref="fileInput"
            type="file"
            accept=".xlsx,.xls"
            class="hidden"
            @change="onFileSelected"
          />
        </div>
      </div>
      <div v-if="importError" class="text-red-600 text-sm mb-2">{{ importError }}</div>
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
              <td class="text-right font-medium num" :class="t.type === 'INCOME' ? 'text-emerald-600' : 'text-red-600'">
                {{ krw(t.amount) }}
              </td>
              <td class="muted">{{ t.memo || '-' }}</td>
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

    <!-- 엑셀 임포트 미리보기 모달 -->
    <div
      v-if="showPreview && preview"
      class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      @click.self="closePreview"
    >
      <div class="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        <div class="px-5 py-3 border-b flex items-center justify-between">
          <div class="section-title">임포트 미리보기</div>
          <button class="text-slate-500 hover:text-slate-800" @click="closePreview">✕</button>
        </div>
        <div class="px-5 py-3 bg-slate-50 border-b flex flex-wrap gap-4 text-sm">
          <span>전체: <b>{{ preview.total }}</b>건</span>
          <span class="text-emerald-600">유효: <b>{{ preview.valid_count }}</b>건</span>
          <span class="text-red-600">오류: <b>{{ preview.error_count }}</b>건</span>
          <span class="text-slate-500 ml-auto">유효한 행만 저장됩니다</span>
        </div>
        <div class="overflow-auto flex-1 px-5 py-3">
          <table class="table text-sm">
            <thead>
              <tr>
                <th class="w-12">행</th>
                <th>날짜</th>
                <th>구분</th>
                <th>내용</th>
                <th class="text-right">금액</th>
                <th>카테고리</th>
                <th>메모</th>
                <th>상태</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in preview.rows"
                :key="r.row_number"
                :class="r.valid ? '' : 'bg-red-50'"
              >
                <td class="muted num">{{ r.row_number }}</td>
                <td>{{ r.date || '-' }}</td>
                <td>
                  <span v-if="r.type === 'INCOME'" class="badge-income">수입</span>
                  <span v-else-if="r.type === 'EXPENSE'" class="badge-expense">지출</span>
                  <span v-else>-</span>
                </td>
                <td>{{ r.description || '-' }}</td>
                <td class="text-right num">{{ r.amount ? krw(r.amount) : '-' }}</td>
                <td>{{ r.category_name || '-' }}</td>
                <td class="muted">{{ r.memo || '-' }}</td>
                <td>
                  <span v-if="r.valid" class="text-emerald-600 text-xs">✓ 유효</span>
                  <span v-else class="text-red-600 text-xs">{{ r.errors.join(', ') }}</span>
                </td>
              </tr>
              <tr v-if="!preview.rows.length">
                <td colspan="8" class="text-center text-slate-400 py-6">데이터가 없습니다</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="px-5 py-3 border-t flex items-center justify-end gap-2">
          <button class="btn-secondary" @click="closePreview">취소</button>
          <button
            class="btn-primary"
            :disabled="importing || !preview.valid_count"
            @click="confirmImport"
          >
            {{ importing ? '저장 중...' : `${preview.valid_count}건 저장` }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
