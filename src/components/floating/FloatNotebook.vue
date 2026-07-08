<template>
  <div class="float-notebook">
    <!-- 新建笔记 -->
    <div class="note-input">
      <el-input
        v-model="newNote"
        type="textarea"
        :rows="3"
        placeholder="记录观察、想法、操作计划..."
        size="small"
      />
      <div class="note-meta">
        <span class="strategy-tag" v-if="store.currentStrategy">{{ store.currentStrategy }}</span>
        <el-button size="small" type="primary" @click="saveNote" :disabled="!newNote.trim()">保存</el-button>
      </div>
    </div>

    <el-divider />

    <!-- 笔记列表 -->
    <div class="note-list">
      <div v-if="store.notes.length === 0" class="empty-tip">
        还没有笔记，开始记录你的第一条观察吧
      </div>
      <div v-for="note in store.notes" :key="note.id" class="note-item">
        <div class="note-content">{{ note.content }}</div>
        <div class="note-footer">
          <span class="note-strategy" v-if="note.strategy">{{ note.strategy }}</span>
          <span class="note-time">{{ formatNoteTime(note.createdAt) }}</span>
          <el-icon class="note-del" @click="store.deleteNote(note.id)"><Delete /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { useFloatingStore } from '@/stores/floating'

const store = useFloatingStore()
const newNote = ref('')

function saveNote() {
  if (!newNote.value.trim()) return
  store.addNote(newNote.value.trim())
  newNote.value = ''
}

function formatNoteTime(iso) {
  const d = new Date(iso)
  const now = new Date()
  const diff = (now - d) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${m}-${day} ${h}:${min}`
}
</script>

<style lang="scss" scoped>
.float-notebook {
  .note-input {
    .note-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 6px;

      .strategy-tag {
        font-size: 11px;
        color: #409eff;
        background: rgba(64, 158, 255, 0.1);
        padding: 2px 8px;
        border-radius: 4px;
      }
    }
  }

  .note-list {
    max-height: 300px;
    overflow-y: auto;

    .empty-tip {
      text-align: center;
      color: var(--text-color-secondary);
      font-size: 12px;
      padding: 20px 0;
    }

    .note-item {
      padding: 8px 10px;
      border-radius: 6px;
      background: var(--bg-color);
      margin-bottom: 8px;

      .note-content {
        font-size: 13px;
        color: var(--text-color);
        line-height: 1.5;
        word-break: break-all;
      }

      .note-footer {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 6px;

        .note-strategy {
          font-size: 11px;
          color: #409eff;
        }

        .note-time {
          font-size: 11px;
          color: var(--text-color-secondary);
          flex: 1;
        }

        .note-del {
          cursor: pointer;
          color: var(--text-color-secondary);
          font-size: 14px;

          &:hover {
            color: var(--el-color-danger);
          }
        }
      }
    }
  }
}
</style>
