import { defineStore } from 'pinia'

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessionId: '',
    selectedStocks: [] as string[],
    gameResult: null as any,
  }),
  actions: {
    setSessionId(id: string) {
      this.sessionId = id
    },
    setSelectedStocks(stocks: string[]) {
      this.selectedStocks = stocks
    },
    setGameResult(result: any) {
      this.gameResult = result
    },
  },
})
