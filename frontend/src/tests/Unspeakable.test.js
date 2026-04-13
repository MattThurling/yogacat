import { mount, flushPromises } from '@vue/test-utils'
import Unspeakable from '@/Unspeakable.vue'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Mock AudioContext globally
globalThis.AudioContext = vi.fn().mockImplementation(() => ({
  createOscillator: vi.fn().mockReturnValue({
    connect: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    frequency: { setValueAtTime: vi.fn() }
  }),
  createGain: vi.fn().mockReturnValue({
    connect: vi.fn(),
    gain: { setValueAtTime: vi.fn() }
  }),
  destination: {},
  close: vi.fn()
}));

vi.mock('axios')

describe('Unspeakable', () => {
  beforeEach(() => {
    axios.get.mockClear()
  })

  it('loads sets and enables Start button', async () => {
    // Mock available sets
    axios.get.mockImplementation(url => {
      if (url.includes('sets')) {
        return Promise.resolve({
          data: [{ id: 1, name: 'English' }]
        })
      }
      if (url.includes('cards')) {
        return Promise.resolve({
          data: [
            { target: 'apple', taboo_words: ['fruit', 'red', 'tree'] }
          ]
        })
      }
    })

    const wrapper = mount(Unspeakable)

    // Wait for onMounted API calls to finish
    await flushPromises()

    const select = wrapper.find('select')
    await select.setValue('1')
    await flushPromises()

    const startButton = wrapper.find('button')
    expect(startButton.attributes('disabled')).toBeFalsy()
  })
})

vi.mock('@/api', () => ({
  publicApi: {
    get: vi.fn((url) => {
      if (url.includes('sets')) {
        return Promise.resolve({
          data: [{ id: 1, name: 'English Set' }]
        })
      }
      if (url.includes('cards')) {
        return Promise.resolve({
          data: [
            { target: 'apple', taboo_words: ['fruit', 'red', 'tree'] }
          ]
        })
      }
    })
  },
  secureApi: {
    get: vi.fn(),
    post: vi.fn()
  }
}))


