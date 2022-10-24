
const state = {
  columns: Object,
  columnsMap: new Map()
}

const getters = {
  columns: state => state.columns
}

const mutations = {
  INITIATE_COLUMNS () {
    const cookieArr = document.cookie.split('; ')
    let decodedCookie
    for (let i = 0; i < cookieArr.length; i++) {
      const cookiePair = cookieArr[i].split('=')
      if (cookiePair[0].trim() === 'columns') {
        decodedCookie = cookiePair[1]
      }
    }
    if (decodedCookie) {
      const columnsCookie = JSON.parse(decodedCookie)
      for (const [key, value] of new Map(Object.entries(columnsCookie))) {
        state.columnsMap.set(key, value)
      }
      state.columns = columnsCookie
    }
  },
  SET_COLUMNS (state, columns) {
    for (const [key, value] of columns) {
      state.columnsMap.set(key, value)
    }
    document.cookie = 'columns=' + JSON.stringify(Object.fromEntries(state.columnsMap))
    state.columns = Object.fromEntries(state.columnsMap)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations
}
