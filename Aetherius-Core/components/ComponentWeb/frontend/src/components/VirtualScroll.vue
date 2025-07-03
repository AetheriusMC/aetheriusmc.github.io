<template>
  <div
    ref="containerRef"
    class="virtual-scroll-container"
    :style="{ height: containerHeight + 'px' }"
    @scroll="handleScroll"
  >
    <div
      class="virtual-scroll-spacer"
      :style="{ height: totalHeight + 'px' }"
    >
      <div
        class="virtual-scroll-content"
        :style="{ transform: `translateY(${offsetY}px)` }"
      >
        <div
          v-for="(item, index) in visibleItems"
          :key="getItemKey ? getItemKey(item, index + startIndex) : index + startIndex"
          :style="{ height: itemHeight + 'px' }"
          class="virtual-scroll-item"
        >
          <slot :item="item" :index="index + startIndex" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

interface Props {
  items: any[]
  itemHeight: number
  containerHeight: number
  overscan?: number
  getItemKey?: (item: any, index: number) => string | number
}

const props = withDefaults(defineProps<Props>(), {
  overscan: 5,
  getItemKey: undefined
})

const emit = defineEmits<{
  scroll: [scrollTop: number, scrollLeft: number]
  visibleRangeChange: [startIndex: number, endIndex: number]
}>()

const containerRef = ref<HTMLElement>()
const scrollTop = ref(0)

// Calculate visible range
const startIndex = computed(() => {
  const start = Math.floor(scrollTop.value / props.itemHeight) - props.overscan
  return Math.max(0, start)
})

const endIndex = computed(() => {
  const visibleCount = Math.ceil(props.containerHeight / props.itemHeight)
  const end = startIndex.value + visibleCount + props.overscan * 2
  return Math.min(props.items.length - 1, end)
})

const visibleItems = computed(() => {
  return props.items.slice(startIndex.value, endIndex.value + 1)
})

const totalHeight = computed(() => {
  return props.items.length * props.itemHeight
})

const offsetY = computed(() => {
  return startIndex.value * props.itemHeight
})

const handleScroll = (event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
  emit('scroll', target.scrollTop, target.scrollLeft)
}

// Watch for visible range changes
watch([startIndex, endIndex], ([newStart, newEnd]) => {
  emit('visibleRangeChange', newStart, newEnd)
})

// Auto-scroll to bottom function
const scrollToBottom = () => {
  if (containerRef.value) {
    containerRef.value.scrollTop = totalHeight.value
  }
}

// Scroll to specific index
const scrollToIndex = (index: number) => {
  if (containerRef.value) {
    const scrollTop = index * props.itemHeight
    containerRef.value.scrollTop = scrollTop
  }
}

// Check if scrolled to bottom
const isScrolledToBottom = computed(() => {
  if (!containerRef.value) return false
  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  return Math.abs(scrollHeight - clientHeight - scrollTop) < 10
})

defineExpose({
  scrollToBottom,
  scrollToIndex,
  isScrolledToBottom
})

onMounted(() => {
  // Initial setup if needed
})

onUnmounted(() => {
  // Cleanup if needed
})
</script>

<style scoped>
.virtual-scroll-container {
  overflow: auto;
  position: relative;
}

.virtual-scroll-spacer {
  position: relative;
}

.virtual-scroll-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
}

.virtual-scroll-item {
  box-sizing: border-box;
}

/* Custom scrollbar */
.virtual-scroll-container::-webkit-scrollbar {
  width: 8px;
}

.virtual-scroll-container::-webkit-scrollbar-track {
  background: #2d2d2d;
  border-radius: 4px;
}

.virtual-scroll-container::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.virtual-scroll-container::-webkit-scrollbar-thumb:hover {
  background: #777;
}
</style>