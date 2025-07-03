import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ApiClient, apiCall } from '@/utils/api'
import type { PlayerResponse } from '@/types'

export interface PlayerSearchParams {
  query?: string
  page?: number
  per_page?: number
  online_only?: boolean
  game_mode?: string
  min_level?: number | null
  max_level?: number | null
  sort_by?: string
  sort_order?: string
}

export interface PlayerSearchResults {
  players: PlayerResponse[]
  total_count: number
  page: number
  per_page: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface PlayerOperationResult {
  success: boolean
  message: string
  timestamp: string
  player?: string
  action?: string
}

export interface BatchOperationResult {
  success: boolean
  total_players: number
  successful_operations: number
  failed_operations: number
  results: Array<{
    player_uuid: string
    success: boolean
    message: string
    error?: string
  }>
  timestamp: string
  action: string
}

export const usePlayersStore = defineStore('players', () => {
  // State
  const searchResults = ref<PlayerSearchResults>({
    players: [],
    total_count: 0,
    page: 1,
    per_page: 20,
    total_pages: 0,
    has_next: false,
    has_prev: false
  })
  
  const currentPlayer = ref<PlayerResponse | null>(null)
  const playerDetails = ref<PlayerResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastSearchParams = ref<PlayerSearchParams>({})

  // Computed
  const onlinePlayers = computed(() => 
    searchResults.value.players.filter(player => player.online)
  )
  
  const totalPlayers = computed(() => searchResults.value.total_count)
  const onlineCount = computed(() => onlinePlayers.value.length)
  
  const hasPrevPage = computed(() => searchResults.value.has_prev)
  const hasNextPage = computed(() => searchResults.value.has_next)
  const currentPage = computed(() => searchResults.value.page)
  const totalPages = computed(() => searchResults.value.total_pages)

  // Actions
  async function searchPlayers(params: PlayerSearchParams = {}) {
    loading.value = true
    error.value = null
    lastSearchParams.value = params

    const { data, error: apiError } = await apiCall(
      () => ApiClient.searchPlayers({
        page: params.page || 1,
        per_page: params.per_page || 20,
        query: params.query,
        online_only: params.online_only,
        game_mode: params.game_mode,
        min_level: params.min_level,
        max_level: params.max_level,
        sort_by: params.sort_by || 'last_login',
        sort_order: params.sort_order || 'desc'
      }),
      'Failed to search players'
    )

    if (data) {
      searchResults.value = data
    } else if (apiError) {
      error.value = apiError.error
    }

    loading.value = false
    return data !== null
  }

  async function getPlayerDetails(playerIdentifier: string) {
    loading.value = true
    error.value = null

    const { data, error: apiError } = await apiCall(
      () => ApiClient.getPlayerDetails(playerIdentifier),
      `Failed to get details for player ${playerIdentifier}`
    )

    if (data) {
      playerDetails.value = data
      currentPlayer.value = data
    } else if (apiError) {
      error.value = apiError.error
    }

    loading.value = false
    return data
  }

  async function executePlayerAction(
    playerIdentifier: string,
    action: string,
    reason?: string,
    duration?: number
  ): Promise<PlayerOperationResult | null> {
    loading.value = true
    error.value = null

    const { data, error: apiError } = await apiCall(
      () => ApiClient.executePlayerAction(playerIdentifier, {
        action,
        reason,
        duration
      }),
      `Failed to execute ${action} on player ${playerIdentifier}`
    )

    if (data) {
      // Update player in search results if it exists
      updatePlayerInResults(playerIdentifier, action)
    } else if (apiError) {
      error.value = apiError.error
    }

    loading.value = false
    return data
  }

  async function executeBatchPlayerAction(
    playerUuids: string[],
    action: string,
    reason?: string,
    duration?: number
  ): Promise<BatchOperationResult | null> {
    loading.value = true
    error.value = null

    const { data, error: apiError } = await apiCall(
      () => ApiClient.executeBatchPlayerAction({
        player_uuids: playerUuids,
        action,
        reason,
        duration
      }),
      `Failed to execute batch ${action} on ${playerUuids.length} players`
    )

    if (data) {
      // Update players in search results
      playerUuids.forEach(uuid => updatePlayerInResults(uuid, action))
    } else if (apiError) {
      error.value = apiError.error
    }

    loading.value = false
    return data
  }

  async function refreshCurrentSearch() {
    if (Object.keys(lastSearchParams.value).length > 0) {
      await searchPlayers(lastSearchParams.value)
    } else {
      await searchPlayers()
    }
  }

  function updatePlayerInResults(playerIdentifier: string, action: string) {
    const players = searchResults.value.players
    const playerIndex = players.findIndex(p => 
      p.uuid === playerIdentifier || p.name === playerIdentifier
    )
    
    if (playerIndex === -1) return
    
    const player = players[playerIndex]
    
    // Update player state based on action
    switch (action) {
      case 'kick':
        player.online = false
        break
      case 'ban':
        player.is_banned = true
        player.online = false
        break
      case 'unban':
        player.is_banned = false
        break
      case 'op':
        player.is_op = true
        break
      case 'deop':
        player.is_op = false
        break
    }
    
    // Trigger reactivity
    searchResults.value.players = [...players]
  }

  function clearError() {
    error.value = null
  }

  function setCurrentPlayer(player: PlayerResponse | null) {
    currentPlayer.value = player
  }

  function clearPlayerDetails() {
    playerDetails.value = null
  }

  // Player filtering helpers
  function filterPlayersByStatus(status: 'all' | 'online' | 'offline' | 'banned' | 'op') {
    const allPlayers = searchResults.value.players
    
    switch (status) {
      case 'online':
        return allPlayers.filter(p => p.online)
      case 'offline':
        return allPlayers.filter(p => !p.online)
      case 'banned':
        return allPlayers.filter(p => p.is_banned)
      case 'op':
        return allPlayers.filter(p => p.is_op)
      default:
        return allPlayers
    }
  }

  function getPlayersByGameMode(gameMode: string) {
    return searchResults.value.players.filter(p => p.game_mode === gameMode)
  }

  function getPlayersByLevelRange(minLevel: number, maxLevel: number) {
    return searchResults.value.players.filter(p => 
      p.level >= minLevel && p.level <= maxLevel
    )
  }

  // Statistics
  function getPlayerStatistics() {
    const players = searchResults.value.players
    
    return {
      total: players.length,
      online: players.filter(p => p.online).length,
      offline: players.filter(p => !p.online).length,
      banned: players.filter(p => p.is_banned).length,
      ops: players.filter(p => p.is_op).length,
      gameModeCounts: {
        survival: players.filter(p => p.game_mode === 'survival').length,
        creative: players.filter(p => p.game_mode === 'creative').length,
        adventure: players.filter(p => p.game_mode === 'adventure').length,
        spectator: players.filter(p => p.game_mode === 'spectator').length
      },
      averageLevel: players.length > 0 
        ? players.reduce((sum, p) => sum + p.level, 0) / players.length 
        : 0,
      totalPlaytime: players.reduce((sum, p) => sum + (p.playtime_hours || 0), 0)
    }
  }

  return {
    // State
    searchResults,
    currentPlayer,
    playerDetails,
    loading,
    error,
    lastSearchParams,

    // Computed
    onlinePlayers,
    totalPlayers,
    onlineCount,
    hasPrevPage,
    hasNextPage,
    currentPage,
    totalPages,

    // Actions
    searchPlayers,
    getPlayerDetails,
    executePlayerAction,
    executeBatchPlayerAction,
    refreshCurrentSearch,
    updatePlayerInResults,
    clearError,
    setCurrentPlayer,
    clearPlayerDetails,

    // Helpers
    filterPlayersByStatus,
    getPlayersByGameMode,
    getPlayersByLevelRange,
    getPlayerStatistics
  }
})