'''
views/Home.vue
首页组件，显示欢迎信息和导航链接。
'''
<template>
  <div class="home">
    <h1>Welcome to ChatDev</h1>
    <router-link to="/login">Login</router-link> |
    <router-link to="/register">Register</router-link>
  </div>
</template>
<script>
export default {
  name: 'Home',
};
</script>