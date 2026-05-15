import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/components/PdfJsPageViewer.vue', () => ({
  default: {
    name: 'PdfJsPageViewer',
    template: '<div />',
  },
}))

import router from '@/router'
import { useAuthStore } from '@/stores/auth'

async function navigateTo(path) {
  await router.push(path)
  await router.isReady()
}

function setAuthenticatedUser(roles) {
  const authStore = useAuthStore()
  authStore.token = 'test-token'
  authStore.user = {
    id: 'user-1',
    username: 'page-user',
    roles,
    permissions: [],
  }
}

describe('page access routes', () => {
  beforeEach(async () => {
    setActivePinia(createPinia())
    localStorage.clear()
    await router.push('/')
  })

  it('allows a regular authenticated user to open page detail and viewer routes', async () => {
    setAuthenticatedUser(['user'])

    await navigateTo('/records/r1/pages/p1')
    expect(router.currentRoute.value.fullPath).toBe('/records/r1/pages/p1')

    await navigateTo('/records/r1/pages/p1/viewer')
    expect(router.currentRoute.value.fullPath).toBe('/records/r1/pages/p1/viewer')
  })

  it('allows user_scan to open page creation and edit routes', async () => {
    setAuthenticatedUser(['user_scan'])

    await navigateTo('/records/r1/pages/new')
    expect(router.currentRoute.value.fullPath).toBe('/records/r1/pages/new')

    await navigateTo('/records/r1/pages/p1/edit')
    expect(router.currentRoute.value.fullPath).toBe('/records/r1/pages/p1/edit')
  })

  it('allows user_page to open page edit route but not page creation', async () => {
    setAuthenticatedUser(['user_page'])

    await navigateTo('/records/r1/pages/p1/edit')
    expect(router.currentRoute.value.fullPath).toBe('/records/r1/pages/p1/edit')

    await navigateTo('/records/r1/pages/new')
    expect(router.currentRoute.value.name).toBe('Home')
  })
})