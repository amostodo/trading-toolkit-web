<template>
  <div class="formula-recall">
    <div class="recall-header" @click="expanded = !expanded">
      <el-icon><EditPen /></el-icon>
      <span class="recall-title">公式回忆</span>
      <span class="recall-hint">填空练习，强化记忆</span>
      <el-icon class="toggle-icon" :class="{ expanded }"><ArrowDown /></el-icon>
    </div>
    <transition name="expand">
      <div v-show="expanded" class="recall-body">
        <div v-for="(item, idx) in items" :key="idx" class="recall-item">
          <div class="recall-prompt">{{ item.prompt }}</div>
          <el-input
            v-model="answers[idx]"
            size="small"
            :placeholder="item.placeholder || '输入缺失部分'"
            @blur="checkAnswer(idx)"
          >
            <template #append>
              <el-icon :class="{ correct: results[idx] === true, wrong: results[idx] === false }">
                <Check v-if="results[idx] === true" />
                <Close v-else-if="results[idx] === false" />
                <QuestionFilled v-else />
              </el-icon>
            </template>
          </el-input>
          <div v-if="results[idx] !== null && results[idx] !== undefined" class="recall-answer">
            正确答案：<code>{{ item.answer }}</code>
          </div>
        </div>
        <el-button size="small" @click="resetAnswers" class="reset-btn">重置</el-button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { EditPen, ArrowDown, Check, Close, QuestionFilled } from '@element-plus/icons-vue'

const props = defineProps({
  items: { type: Array, default: () => [] }
})

const expanded = ref(false)
const answers = ref(props.items.map(() => ''))
const results = ref(props.items.map(() => null))

function checkAnswer(idx) {
  const user = answers.value[idx].trim()
  if (!user) {
    results.value[idx] = null
    return
  }
  const correct = props.items[idx].answer.trim()
  // 允许数值精度差异
  const userNum = parseFloat(user)
  const correctNum = parseFloat(correct)
  if (!isNaN(userNum) && !isNaN(correctNum)) {
    results.value[idx] = Math.abs(userNum - correctNum) < 0.01
  } else {
    results.value[idx] = user === correct || user.includes(correct)
  }
}

function resetAnswers() {
  answers.value = props.items.map(() => '')
  results.value = props.items.map(() => null)
}
</script>

<style lang="scss" scoped>
.formula-recall {
  background: var(--bg-color-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;

  .recall-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    cursor: pointer;
    user-select: none;

    .recall-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-color);
    }

    .recall-hint {
      font-size: 12px;
      color: var(--text-color-secondary);
      flex: 1;
    }

    .toggle-icon {
      transition: transform 0.2s;
      color: var(--text-color-secondary);

      &.expanded {
        transform: rotate(180deg);
      }
    }
  }

  .recall-body {
    padding: 0 14px 14px;

    .recall-item {
      margin-bottom: 10px;

      .recall-prompt {
        font-size: 13px;
        color: var(--text-color);
        margin-bottom: 4px;
      }

      .recall-answer {
        font-size: 12px;
        color: var(--el-color-success);
        margin-top: 2px;

        code {
          font-size: 12px;
        }
      }
    }

    .reset-btn {
      margin-top: 4px;
    }
  }
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.2s ease;
}

.expand-enter-from, .expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.correct {
  color: var(--el-color-success) !important;
}

.wrong {
  color: var(--el-color-danger) !important;
}
</style>
