import { mount, flushPromises } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import PageList from './PageList.vue'

const mockRoute = {
  params: {
    recordId: 'record-1',
  },
}

const mockAuthStore = {
  hasRole: vi.fn(),
}

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => mockAuthStore,
}))

vi.mock('@/services/page', () => ({
  pageService: {
    listPages: vi.fn(),
    updatePage: vi.fn(),
    startOcr: vi.fn(),
    deletePage: vi.fn(),
  },
}))

vi.mock('@/services/record', () => ({
  recordService: {
    getRecord: vi.fn(),
  },
}))

import { pageService } from '@/services/page'
import { recordService } from '@/services/record'

function createPage(id, order) {
  return {
    id,
    name: `Page ${order}`,
    description: `Description ${order}`,
    page: `Content ${order}`,
    comment: `Comment ${order}`,
    restriction_id: `restriction-${order}`,
    workstatus_id: `workstatus-${order}`,
    order_by: order,
    rotation: 0,
    location_file: null,
    ocr_status: 'completed',
    created_on: '2024-01-01T12:00:00Z',
  }
}

function translate(key, params = {}) {
  if (key === 'pages.currentPosition') {
    return `Position ${params.position}`
  }

  if (key === 'pages.invalidTargetPosition') {
    return `Please enter a position between 1 and ${params.total}.`
  }

  return key
}

async function mountPageList(roles, pages) {
  mockAuthStore.hasRole.mockImplementation((role) => roles.includes(role))
  recordService.getRecord.mockResolvedValue({ title: 'Record Title' })
  pageService.updatePage.mockResolvedValue({})
  pageService.listPages.mockImplementation(async () => ({
    items: pages.map((page) => ({ ...page })),
    total: pages.length,
  }))

  const wrapper = mount(PageList, {
    global: {
      mocks: {
        $t: translate,
        $i18n: { locale: 'de' },
      },
      stubs: {
        RouterLink: {
          template: '<a><slot /></a>',
        },
      },
    },
  })

  await flushPromises()
  await flushPromises()

  return wrapper
}

describe('PageList.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders one grouped reorder block per page for user_page', async () => {
    const pages = [createPage('page-1', 1), createPage('page-2', 2)]
    const wrapper = await mountPageList(['user_page'], pages)

    const panels = wrapper.findAll('.page-reorder-panel')
    expect(panels).toHaveLength(2)

    const firstPanel = panels[0]
    expect(firstPanel.text()).toContain('pages.reorderSectionTitle')
    expect(firstPanel.findAll('.page-order-buttons button')).toHaveLength(2)
    expect(firstPanel.find('input.page-reorder-input').exists()).toBe(true)
    expect(firstPanel.find('button.btn-outline-primary').exists()).toBe(true)
  })

  it('does not render the reorder block for user_scan only', async () => {
    const pages = [createPage('page-1', 1)]
    const wrapper = await mountPageList(['user_scan'], pages)

    expect(wrapper.find('.page-reorder-panel').exists()).toBe(false)
  })

  it('updates affected pages when moving a page to a target position', async () => {
    const pages = [
      createPage('page-1', 1),
      createPage('page-2', 2),
      createPage('page-3', 3),
    ]
    const wrapper = await mountPageList(['admin'], pages)

    await wrapper.find('#move-target-page-3').setValue('1')
    await wrapper.findAll('button.btn-outline-primary')[2].trigger('click')
    await flushPromises()
    await flushPromises()

    expect(pageService.updatePage).toHaveBeenCalledTimes(3)
    expect(pageService.updatePage).toHaveBeenNthCalledWith(
      1,
      'page-3',
      expect.objectContaining({ order_by: 1, name: 'Page 3' })
    )
    expect(pageService.updatePage).toHaveBeenNthCalledWith(
      2,
      'page-1',
      expect.objectContaining({ order_by: 2, name: 'Page 1' })
    )
    expect(pageService.updatePage).toHaveBeenNthCalledWith(
      3,
      'page-2',
      expect.objectContaining({ order_by: 3, name: 'Page 2' })
    )
  })

  it('shows an error and does not update pages for an invalid target position', async () => {
    const pages = [createPage('page-1', 1), createPage('page-2', 2)]
    const wrapper = await mountPageList(['admin'], pages)

    await wrapper.find('#move-target-page-1').setValue('0')
    await wrapper.findAll('button.btn-outline-primary')[0].trigger('click')
    await flushPromises()

    expect(pageService.updatePage).not.toHaveBeenCalled()
    expect(wrapper.vm.error).toBe('Please enter a position between 1 and 2.')
    expect(wrapper.text()).toContain('Please enter a position between 1 and 2.')
  })
})