'''
main.js
主入口文件，初始化Vue应用程序并加载所有必要的组件。
'''
import Vue from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
Vue.config.productionTip = false;
new Vue({
  router,
  store,
  render: h => h(App),
}).$mount('#app');