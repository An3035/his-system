export function formatDate(time: string | Date | null | undefined): string {
  if (!time) return '-'
  const d = new Date(time)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}