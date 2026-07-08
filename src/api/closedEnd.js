import api from './index'

export const closedEndApi = {
  list(params) {
    return api.get('/api/v1/closed-end/list', { params })
  },
  summary() {
    return api.get('/api/v1/closed-end/summary')
  }
}
