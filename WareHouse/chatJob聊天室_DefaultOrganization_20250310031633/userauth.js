'''
store/modules/UserAuth.js
Vuex模块，管理用户认证状态和操作。
'''
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
const state = {
  username: '',
  isAuthenticated: false,
  token: '',
};
const mutations = {
  SET_USERNAME(state, username) {
    state.username = username;
  },
  SET_AUTHENTICATED(state, isAuthenticated) {
    state.isAuthenticated = isAuthenticated;
  },
  SET_TOKEN(state, token) {
    state.token = token;
  },
};
const actions = {
  async login({ commit }, { username, password }) {
    // 模拟从数据库获取用户信息
    const user = { username, password: await bcrypt.hash('password', 10) }; // 假设数据库中存储的是哈希后的密码
    const isMatch = await bcrypt.compare(password, user.password);
    if (isMatch) {
      const token = jwt.sign({ username }, 'YOUR_SECRET_KEY', { expiresIn: '1h' });
      commit('SET_USERNAME', username);
      commit('SET_AUTHENTICATED', true);
      commit('SET_TOKEN', token);
    } else {
      throw new Error('Invalid credentials');
    }
  },
  async register({ commit }, { username, password }) {
    const hashedPassword = await bcrypt.hash(password, 10);
    // 模拟将用户信息存储到数据库
    const token = jwt.sign({ username }, 'YOUR_SECRET_KEY', { expiresIn: '1h' });
    commit('SET_USERNAME', username);
    commit('SET_AUTHENTICATED', true);
    commit('SET_TOKEN', token);
  },
};
export default {
  namespaced: true,
  state,
  mutations,
  actions,
};