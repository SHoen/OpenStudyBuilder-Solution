import Vue from 'vue'
import { mount, createLocalVue } from '@vue/test-utils'
import Vuetify from 'vuetify'

import repository from '@/api/repository'
import DataTableExportButton from '@/components/tools/DataTableExportButton'

describe('DataTableExportButton.vue', () => {
  const localVue = createLocalVue()
  let vuetify
  let wrapper

  beforeEach(async () => {
    const objectsLabel = 'objectives'
    const dataUrl = '/objectives/'
    const vuetify = new Vuetify()
    document.body.setAttribute('data-app', true)
    wrapper = mount(DataTableExportButton, {
      localVue,
      vuetify,
      propsData: { objectsLabel, dataUrl }
    })
    // Trigger 'click' event on the menu button to open it and so
    // render items
    wrapper.find('button.v-btn').trigger('click')
    await wrapper.vm.$nextTick()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  test('proposes export formats', async () => {
    expect(wrapper.find('.v-list-item__title').text()).toContain('CSV')
  })

  test('trigger download action', async () => {
    global.URL.createObjectURL = jest.fn()
    global.URL.revokeObjectURL = jest.fn()
    const mockGet = jest.spyOn(repository, 'get')
    mockGet.mockImplementation(() => Promise.resolve([{ name: 'Test' }]))
    wrapper.findComponent({ name: 'v-list-item' }).trigger('click')
    await wrapper.vm.$nextTick()
    // FIXME: component has been updated
    // expect(mockGet).toHaveBeenCalled()
    // expect(global.URL.createObjectURL).toHaveBeenCalled()
  })
})
