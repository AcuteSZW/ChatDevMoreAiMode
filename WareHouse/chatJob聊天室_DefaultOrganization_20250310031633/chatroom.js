'''
store/modules/ChatRoom.js
Vuex模块，管理聊天室状态和操作。
'''
const state = {
  messages: [],
};
const mutations = {
  ADD_MESSAGE(state, message) {
    state.messages.push(message);
  },
};
const actions = {
  sendMessage({ commit }, message) {
    commit('ADD_MESSAGE', message);
  },
};
export default {
  namespaced: true,
  state,
  mutations,
  actions,
};