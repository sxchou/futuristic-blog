import { nextTick, type Ref } from 'vue'

export async function updateArrayItem<T extends { id: number }>(
  array: Ref<T[]>,
  id: number,
  updateFn: () => Promise<T>
): Promise<T> {
  const index = array.value.findIndex(item => item.id === id)
  if (index === -1) {
    throw new Error(`Item with id ${id} not found`)
  }
  
  const updatedItem = await updateFn()
  const newArray = [...array.value]
  newArray[index] = updatedItem
  array.value = newArray
  await nextTick()
  
  return updatedItem
}

export async function addArrayItem<T>(
  array: Ref<T[]>,
  createFn: () => Promise<T>
): Promise<T> {
  const newItem = await createFn()
  array.value = [...array.value, newItem]
  await nextTick()
  
  return newItem
}

export async function removeArrayItem<T extends { id: number }>(
  array: Ref<T[]>,
  id: number
): Promise<void> {
  const index = array.value.findIndex(item => item.id === id)
  if (index === -1) return
  
  const newArray = [...array.value]
  newArray.splice(index, 1)
  array.value = newArray
  await nextTick()
}

export async function optimisticUpdate<T extends { id: number }>(
  array: Ref<T[]>,
  id: number,
  optimisticData: Partial<T>,
  updateFn: () => Promise<T>
): Promise<T> {
  const index = array.value.findIndex(item => item.id === id)
  if (index === -1) {
    throw new Error(`Item with id ${id} not found`)
  }
  
  const originalItem = { ...array.value[index] }
  
  try {
    const optimisticItem = { ...array.value[index], ...optimisticData }
    const optimisticArray = [...array.value]
    optimisticArray[index] = optimisticItem
    array.value = optimisticArray
    await nextTick()
    
    const updatedItem = await updateFn()
    
    const finalArray = [...array.value]
    finalArray[index] = updatedItem
    array.value = finalArray
    await nextTick()
    
    return updatedItem
  } catch (error) {
    const rollbackArray = [...array.value]
    rollbackArray[index] = originalItem
    array.value = rollbackArray
    await nextTick()
    
    throw error
  }
}

export async function toggleItemStatus<T extends { id: number; is_active: boolean }>(
  array: Ref<T[]>,
  id: number,
  toggleFn: (newStatus: boolean) => Promise<T>
): Promise<T> {
  const index = array.value.findIndex(item => item.id === id)
  if (index === -1) {
    throw new Error(`Item with id ${id} not found`)
  }
  
  const currentStatus = array.value[index].is_active
  const newStatus = !currentStatus
  
  return optimisticUpdate(
    array,
    id,
    { is_active: newStatus } as Partial<T>,
    () => toggleFn(newStatus)
  )
}
