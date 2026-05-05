import { ref } from 'vue'
import { deletionPreviewApi } from '@/api/deletionPreview'
import type { DeletionPreview } from '@/api/deletionPreview'

export function useDeletionConfirm() {
  const showDeletionDialog = ref(false)
  const deletionPreview = ref<DeletionPreview | null>(null)
  const deletionLoading = ref(false)
  const currentItemType = ref('')
  const currentItemId = ref(0)

  const requestDeletion = async (itemType: string, itemId: number, itemName?: string): Promise<boolean> => {
    currentItemType.value = itemType
    currentItemId.value = itemId
    deletionLoading.value = true
    showDeletionDialog.value = true

    try {
      deletionPreview.value = await deletionPreviewApi.preview(itemType, itemId)
      return true
    } catch {
      deletionPreview.value = {
        item_type: itemType,
        item_type_label: itemType,
        item_id: itemId,
        item_name: itemName || `#${itemId}`,
        can_delete: true,
        block_reason: null,
        associated_items: [],
        total_affected: 0,
      }
      return true
    } finally {
      deletionLoading.value = false
    }
  }

  const confirmDeletion = () => {
    showDeletionDialog.value = false
  }

  const cancelDeletion = () => {
    showDeletionDialog.value = false
    deletionPreview.value = null
  }

  return {
    showDeletionDialog,
    deletionPreview,
    deletionLoading,
    currentItemType,
    currentItemId,
    requestDeletion,
    confirmDeletion,
    cancelDeletion,
  }
}
