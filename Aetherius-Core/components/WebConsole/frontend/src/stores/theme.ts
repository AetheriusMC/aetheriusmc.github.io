import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export type Theme = 'light' | 'dark' | 'system'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<Theme>('system')
  const systemTheme = ref<'light' | 'dark'>('light')
  
  const isDark = computed(() => {
    if (theme.value === 'system') {
      return systemTheme.value === 'dark'
    }
    return theme.value === 'dark'
  })
  
  const effectiveTheme = computed(() => {
    if (theme.value === 'system') {
      return systemTheme.value
    }
    return theme.value
  })

  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    applyTheme()
  }

  const applyTheme = () => {
    const root = document.documentElement
    
    if (isDark.value) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    
    // Update meta theme-color
    const metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (metaThemeColor) {
      metaThemeColor.setAttribute(
        'content', 
        isDark.value ? '#1f2937' : '#ffffff'
      )
    }
  }

  const initializeTheme = () => {
    // Load saved theme from localStorage
    const savedTheme = localStorage.getItem('theme') as Theme
    if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
      theme.value = savedTheme
    }
    
    // Detect system theme
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemTheme.value = mediaQuery.matches ? 'dark' : 'light'
    
    // Listen for system theme changes
    mediaQuery.addEventListener('change', (e) => {
      systemTheme.value = e.matches ? 'dark' : 'light'
    })
    
    // Apply initial theme
    applyTheme()
  }

  // Watch for theme changes and apply them
  watch([theme, systemTheme], applyTheme)

  return {
    theme: computed(() => theme.value),
    systemTheme: computed(() => systemTheme.value),
    isDark,
    effectiveTheme,
    setTheme,
    initializeTheme
  }
})