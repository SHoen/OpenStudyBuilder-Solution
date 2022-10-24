import { mount, createLocalVue } from '@vue/test-utils'
import Vuetify from 'vuetify'

import NotApplicableField from '@/components/tools/NotApplicableField'

describe('NotApplicableField', () => {
  const localVue = createLocalVue()
  const cleanFunc = jest.fn()
  const label = 'My field'
  const hint = 'My field hint'
  let vuetify
  let wrapper

  beforeEach(async () => {
    const vuetify = new Vuetify()
    document.body.setAttribute('data-app', true)
    wrapper = mount(NotApplicableField, {
      localVue,
      vuetify,
      propsData: { label, hint, cleanFunction: cleanFunc, checked: false }
    })
  })

  test('Label is displayed', async () => {
    expect(wrapper.find('label').text()).toBe(label)
  })
  test('Checkbox is there', async () => {
    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true)
  })
  test('Check if clean function is called', async () => {
    wrapper.find('input[type="checkbox"]').trigger('click')
    await wrapper.vm.$nextTick()
    expect(cleanFunc).toHaveBeenCalled()
  })
})
