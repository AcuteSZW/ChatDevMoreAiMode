'''
views/ChatRoom.vue
聊天室组件，显示聊天界面和处理聊天功能。
'''
<template>
  <div class="chatroom">
    <h1>Chat Room</h1>
    <div class="messages">
      <div v-for="message in messages" :key="message.id" class="message">
        <strong>{{ message.username }}:</strong> {{ message.text }}
      </div>
    </div>
    <input type="text" v-model="newMessage" @keyup.enter="sendMessage" placeholder="Type a message...">
    <button @click="sendToAI">Ask AI</button>
  </div>
</template>
<script>
import axios from 'axios';
export default {
  name: 'ChatRoom',
  data() {
    return {
      newMessage: '',
      messages: [],
    };
  },
  methods: {
    sendMessage() {
      if (this.newMessage.trim() !== '') {
        this.$store.dispatch('ChatRoom/sendMessage', { username: this.$store.state.UserAuth.username, text: this.newMessage });
        this.newMessage = '';
      }
    },
    async sendToAI() {
      if (this.newMessage.trim() !== '') {
        try {
          const response = await axios.post('/api/ai', { message: this.newMessage }, {
            headers: {
              'Authorization': `Bearer ${this.$store.state.UserAuth.token}`,
            },
          });
          this.$store.dispatch('ChatRoom/sendMessage', { username: 'AI', text: response.data.reply });
          this.newMessage = '';
        } catch (error) {
          console.error('Error communicating with AI:', error);
        }
      }
    },
  },
  created() {
    this.$store.subscribe((mutation, state) => {
      if (mutation.type === 'ChatRoom/ADD_MESSAGE') {
        this.messages = state.ChatRoom.messages;
      }
    });
  },
};
</script>
<style scoped>
.messages {
  height: 300px;
  overflow-y: scroll;
  border: 1px solid #ccc;
  padding: 10px;
  margin-bottom: 10px;
}
.message {
  margin-bottom: 5px;
}
</style>