import { defineStore } from 'pinia'

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessionId: '',
    selectedStocks: [] as string[],
    gameResult: null as {
      total_score?: number
      final_cash?: number
      portfolio_value?: number
      session_id?: string
      player_name?: string
      [key: string]: unknown
    } | null,
    gameData: null as {
      date: { month: number; year: number }
      stockDetails: Array<{
        ticker: string
        type: string
        companyName?: string
        sector?: string
      }>
      playerName?: string
    } | null,
  }),
  actions: {
    setSessionId(id: string) {
      this.sessionId = id
    },
    setSelectedStocks(stocks: string[]) {
      this.selectedStocks = stocks
    },
    setGameResult(
      result: {
        total_score?: number
        final_cash?: number
        portfolio_value?: number
        session_id?: string
        player_name?: string
        [key: string]: unknown
      } | null,
    ) {
      this.gameResult = result
    },
    setGameData(
      data: {
        date: { month: number; year: number }
        stockDetails: Array<{
          ticker: string
          type: string
          companyName?: string
          sector?: string
        }>
        playerName?: string
      } | null,
    ) {
      this.gameData = data
    },
  },
})
