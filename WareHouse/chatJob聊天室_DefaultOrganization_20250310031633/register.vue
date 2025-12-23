'''
views/Register.vue
注册组件，处理用户注册功能。
'''
<template>
  <div class="register">
    <h1>Register</h1>
    <form @submit.prevent="register">
      <input type="text" v-model="username" placeholder="Username" required>
      <input type="password" v-model="password" placeholder="Password" required>
      <button type="submit">Register</button>
    </form>
  </div>
</template>
<script>
export default {
  name: 'Register',
  data() {
    return {
      username: '',
      password: '',
    };
  },
  methods: {
    register() {
      this.$store.dispatch('UserAuth/register', { username: this.username, password: this.password });
    },
  },
};
</script>