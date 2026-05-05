import apiClient from './client'

export interface AssociatedItem {
  type: string
  type_label: string
  id: number | null
  name: string
  detail: string | null
  action: string
  count: number
}

export interface DeletionPreview {
  item_type: string
  item_type_label: string
  item_id: number
  item_name: string
  can_delete: boolean
  block_reason: string | null
  associated_items: AssociatedItem[]
  total_affected: number
}

export interface DetailItem {
  id: number | null
  name: string
  detail: string | null
}

export interface DetailResponse {
  items: DetailItem[]
  total: number
  showing: number
}

export const deletionPreviewApi = {
  async preview(itemType: string, itemId: number): Promise<DeletionPreview> {
    const { data } = await apiClient.get(`/deletion-preview/${itemType}/${itemId}`)
    return data
  },

  async details(
    itemType: string,
    itemId: number,
    assocType: string,
    assocName: string,
    limit: number = 5
  ): Promise<DetailResponse> {
    const { data } = await apiClient.get(`/deletion-preview/${itemType}/${itemId}/details`, {
      params: {
        assoc_type: assocType,
        assoc_name: assocName,
        limit,
      }
    })
    return data
  }
}
