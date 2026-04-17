export const krw = (n) => {
  const num = Number(n ?? 0)
  return num.toLocaleString('ko-KR', { style: 'currency', currency: 'KRW', maximumFractionDigits: 0 })
}

export const num = (n) => Number(n ?? 0).toLocaleString('ko-KR')

export const today = () => new Date().toISOString().slice(0, 10)

export const firstDayOfYear = () => {
  const d = new Date()
  return `${d.getFullYear()}-01-01`
}

export const firstDayOfMonth = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}
