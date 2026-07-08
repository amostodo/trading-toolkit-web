<template>
  <!-- 可拖动工具栏 -->
  <div
    class="float-toolbar"
    :style="{ left: pos.x + 'px', top: pos.y + 'px' }"
    @mousedown="startDrag"
    @touchstart="startDrag"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
  >
    <div class="pet-body" :class="{ active: store.activePanel }" @click.stop="onPetClick">
      <el-icon :size="24"><Coin /></el-icon>
    </div>
    <div class="toolbar-items" v-show="store.activePanel || hovered">
      <div
        v-for="tool in tools"
        :key="tool.key"
        class="tool-item"
        :class="{ active: store.activePanel === tool.key }"
        @click.stop="store.togglePanel(tool.key)"
      >
        <el-icon :size="16"><component :is="tool.icon" /></el-icon>
        <span class="tool-label">{{ tool.label }}</span>
      </div>
    </div>
  </div>

  <!-- 面板容器 -->
  <teleport to="body">
    <div
      v-if="store.activePanel"
      class="float-panel"
      :style="panelStyle"
      @mousedown="startPanelDrag"
      @touchstart="startPanelDrag"
    >
      <div class="panel-header">
        <span class="panel-title">{{ currentTitle }}</span>
        <el-icon class="panel-close" @click="store.closePanel"><Close /></el-icon>
      </div>
      <div class="panel-body">
        <FloatCalculator v-if="store.activePanel === 'calculator'" />
        <FloatNotebook v-else-if="store.activePanel === 'notebook'" />
        <FloatFormula v-else-if="store.activePanel === 'formula'" />
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Coin, Close, Operation, EditPen, Reading } from '@element-plus/icons-vue'
import { useFloatingStore } from '@/stores/floating'
import FloatCalculator from './FloatCalculator.vue'
import FloatNotebook from './FloatNotebook.vue'
import FloatFormula from './FloatFormula.vue'

const store = useFloatingStore()
const hovered = ref(false)

const tools = [
  { key: 'calculator', label: '计算器', icon: Operation },
  { key: 'notebook', label: '笔记', icon: EditPen },
  { key: 'formula', label: '公式库', icon: Reading }
]

const pos = ref({ ...store.position })

const panelPos = ref({ x: 0, y: 0 })
const panelStyle = computed(() => ({
  left: panelPos.value.x + 'px',
  top: panelPos.value.y + 'px'
}))

const currentTitle = computed(() => {
  const t = tools.find(t => t.key === store.activePanel)
  return t ? t.label : ''
})

// 工具栏拖动
let dragging = false
let dragOffset = { x: 0, y: 0 }
let dragStart = { x: 0, y: 0 }
let dragMoved = false

function startDrag(e) {
  // 点击工具项时不拖动
  if (e.target.closest('.tool-item')) return
  dragging = true
  dragMoved = false
  const point = e.touches ? e.touches[0] : e
  dragStart = { x: point.clientX, y: point.clientY }
  dragOffset.x = point.clientX - pos.value.x
  dragOffset.y = point.clientY - pos.value.y
  e.preventDefault()
}

function onDrag(e) {
  if (!dragging) return
  const point = e.touches ? e.touches[0] : e
  // 移动距离 > 5px 视为拖动，避免点击误判
  if (Math.abs(point.clientX - dragStart.x) > 5 || Math.abs(point.clientY - dragStart.y) > 5) {
    dragMoved = true
  }
  const x = Math.max(0, Math.min(window.innerWidth - 50, point.clientX - dragOffset.x))
  const y = Math.max(0, Math.min(window.innerHeight - 50, point.clientY - dragOffset.y))
  pos.value = { x, y }
}

function endDrag() {
  if (dragging) {
    dragging = false
    if (dragMoved) {
      store.updatePosition(pos.value)
    }
  }
}

// 点击宠物本身：拖动结束且未移动则切换工具菜单/面板
function onPetClick() {
  if (dragMoved) return
  // 已打开面板则关闭；否则打开默认（计算器）面板，并展开工具菜单
  if (store.activePanel) {
    store.closePanel()
  } else {
    store.togglePanel('calculator')
  }
}

// 面板拖动
let panelDragging = false
let panelOffset = { x: 0, y: 0 }

function startPanelDrag(e) {
  if (!e.target.closest('.panel-header')) return
  if (e.target.closest('.panel-close')) return
  panelDragging = true
  const point = e.touches ? e.touches[0] : e
  const rect = e.currentTarget.getBoundingClientRect()
  panelOffset.x = point.clientX - rect.left
  panelOffset.y = point.clientY - rect.top
  e.preventDefault()
}

function onPanelDrag(e) {
  if (!panelDragging) return
  const point = e.touches ? e.touches[0] : e
  const x = Math.max(0, Math.min(window.innerWidth - 320, point.clientX - panelOffset.x))
  const y = Math.max(0, Math.min(window.innerHeight - 100, point.clientY - panelOffset.y))
  panelPos.value = { x, y }
}

function endPanelDrag() {
  panelDragging = false
}

// 打开面板时定位到工具栏旁边
function positionPanel() {
  const x = Math.max(10, Math.min(window.innerWidth - 340, pos.value.x - 330))
  const y = Math.max(10, Math.min(window.innerHeight - 400, pos.value.y - 50))
  panelPos.value = { x, y }
}

let hoverTimer = null
function onMouseEnter() {
  clearTimeout(hoverTimer)
  hovered.value = true
}
function onMouseLeave() {
  hoverTimer = setTimeout(() => { hovered.value = false }, 300)
}

onMounted(() => {
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', endDrag)
  window.addEventListener('touchmove', onDrag)
  window.addEventListener('touchend', endDrag)
  window.addEventListener('mousemove', onPanelDrag)
  window.addEventListener('mouseup', endPanelDrag)
  window.addEventListener('touchmove', onPanelDrag)
  window.addEventListener('touchend', endPanelDrag)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', endDrag)
  window.removeEventListener('touchmove', onDrag)
  window.removeEventListener('touchend', endDrag)
  window.removeEventListener('mousemove', onPanelDrag)
  window.removeEventListener('mouseup', endPanelDrag)
  window.removeEventListener('touchmove', onPanelDrag)
  window.removeEventListener('touchend', endPanelDrag)
})

// 监听 activePanel 变化定位面板
import { watch } from 'vue'
watch(() => store.activePanel, (val) => {
  if (val) positionPanel()
})
</script>

<style lang="scss" scoped>
.float-toolbar {
  position: fixed;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  user-select: none;
  cursor: grab;

  &:active {
    cursor: grabbing;
  }

  .pet-body {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: linear-gradient(135deg, #409eff, #66b1ff);
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
    transition: all 0.3s ease;
    animation: float 3s ease-in-out infinite;

    &.active {
      transform: scale(1.1);
      animation: none;
    }

    &:hover {
      animation: none;
      box-shadow: 0 6px 16px rgba(64, 158, 255, 0.6);
    }
  }

  &:hover .pet-body {
    animation: none;
  }

  .toolbar-items {
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: var(--bg-color-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 6px;
    box-shadow: var(--card-shadow);

    .tool-item {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 8px;
      cursor: pointer;
      color: var(--text-color);
      font-size: 12px;
      transition: all 0.2s;
      white-space: nowrap;

      &:hover {
        background: var(--bg-color);
      }

      &.active {
        background: #409eff;
        color: #fff;
      }
    }
  }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.float-panel {
  position: fixed;
  z-index: 10000;
  width: 320px;
  max-height: 480px;
  background: var(--bg-color-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: var(--bg-color);
    cursor: move;
    border-bottom: 1px solid var(--border-color);

    .panel-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-color);
    }

    .panel-close {
      cursor: pointer;
      color: var(--text-color-secondary);
      transition: color 0.2s;

      &:hover {
        color: var(--el-color-danger);
      }
    }
  }

  .panel-body {
    flex: 1;
    overflow-y: auto;
    padding: 12px 14px;
  }
}

:deep(.dark) .pet-body {
  background: linear-gradient(135deg, #66b1ff, #85c1ff);
}
</style>
