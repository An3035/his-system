import { ElMessage } from 'element-plus'

export function showSuccess(msg: string) {
  ElMessage.success(msg)
}

export function showError(msg: string) {
  ElMessage.error(msg)
}