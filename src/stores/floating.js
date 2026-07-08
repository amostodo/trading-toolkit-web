import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getCache, setCache } from '@/utils/cache'

const NOTES_KEY = 'float_notes'
const POSITION_KEY = 'float_position'

export const useFloatingStore = defineStore('floating', () => {
  // 当前激活的面板：null | 'calculator' | 'notebook' | 'formula'
  const activePanel = ref(null)
  // 工具栏位置
  const position = ref(getCache(POSITION_KEY) || { x: window.innerWidth - 80, y: window.innerHeight - 120 })
  // 笔记列表
  const notes = ref(getCache(NOTES_KEY) || [])
  // 当前页面策略（自动绑定）
  const currentStrategy = ref('')

  const hasNotes = computed(() => notes.value.length > 0)

  function togglePanel(panel) {
    activePanel.value = activePanel.value === panel ? null : panel
  }

  function closePanel() {
    activePanel.value = null
  }

  function updatePosition(pos) {
    position.value = pos
    setCache(POSITION_KEY, pos)
  }

  function setStrategy(name) {
    currentStrategy.value = name
  }

  function addNote(content) {
    const note = {
      id: Date.now(),
      content,
      strategy: currentStrategy.value,
      createdAt: new Date().toISOString()
    }
    notes.value.unshift(note)
    saveNotes()
  }

  function deleteNote(id) {
    notes.value = notes.value.filter(n => n.id !== id)
    saveNotes()
  }

  function saveNotes() {
    setCache(NOTES_KEY, notes.value)
  }

  return {
    activePanel, position, notes, currentStrategy, hasNotes,
    togglePanel, closePanel, updatePosition, setStrategy,
    addNote, deleteNote
  }
})
