'''
store/index.js
Vuex store配置文件，管理应用程序的状态。
'''
import Vue from 'vue';
import Vuex from 'vuex';
import UserAuth from './modules/UserAuth';
import ChatRoom from './modules/ChatRoom';
Vue.use(Vuex);
export default new Vuex.Store({
  modules: {
    UserAuth,
    ChatRoom,
  },
});