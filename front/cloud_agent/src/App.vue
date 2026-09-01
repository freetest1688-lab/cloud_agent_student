<template>
  <div class="chat-container">
    <el-container class="app-shell">
      <el-aside width="260px" class="sidebar">
        <div class="sidebar-header">
          <div class="brand">
            <div class="brand-logo">CA</div>
            <h2>Cloud Agent</h2>
          </div>
          <el-button type="primary" :icon="Plus" circle @click="createNewSession" />
        </div>
        <div class="session-list">
          <div 
            v-for="session in sessions" 
            :key="session.id"
            :class="['session-item', { active: currentSessionId === session.id }]"
            @click="switchSession(session.id)"
          >
            <el-icon><ChatDotRound /></el-icon>
            <span class="session-name">{{ session.name }}</span>
          </div>
        </div>
        <div class="user-info">
          <div class="mini-avatar user-avatar">U</div>
          <span class="username">user_1001</span>
        </div>
      </el-aside>

      <el-main class="chat-main">
        <div class="chat-header">
          <div class="header-title">Enterprise Cloud Assistant</div>
          <div class="header-subtitle">Multi-Agent · Billing · Promotion · FinOps</div>
        </div>
        <div class="message-list" ref="messageListRef">
          <div v-if="messages.length === 0" class="empty-state">
            <el-icon size="64" color="#409EFC"><Service /></el-icon>
            <h3 class="welcome-title">Welcome to the Cloud Platform Assistant</h3>
            <p class="welcome-desc">I'm your dedicated AI assistant. Ask me anything, or try one of these common scenarios:</p>

            <div class="scenario-container">
              <el-row :gutter="20">
                <el-col :span="12">
                  <div class="scenario-card">
                    <div class="card-header">
                      <el-icon><Monitor /></el-icon>
                      <span>Product Q&amp;A and Recommendations</span>
                    </div>
                    <div class="scenario-list">
                      <div class="scenario-item" @click="sendQuery('What are the basic properties of ECS cloud servers?')">What are the basic properties of ECS cloud servers?</div>
                      <div class="scenario-item" @click="sendQuery('I run a Java API service + MySQL. Is 8 vCPU / 16 GB enough? Recommend a specific instance type.')">Java service + MySQL: recommend a specific instance type</div>
                    </div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="scenario-card">
                    <div class="card-header">
                      <el-icon><List /></el-icon>
                      <span>Billing &amp; Instance Lookup</span>
                    </div>
                    <div class="scenario-list">
                      <div class="scenario-item" @click="sendQuery('Show me my recent orders')">Show me my recent orders</div>
                      <div class="scenario-item" @click="sendQuery('List all of my running instances')">List all of my running instances</div>
                    </div>
                  </div>
                </el-col>
              </el-row>
              <el-row :gutter="20" style="margin-top: 20px;">
                <el-col :span="12">
                  <div class="scenario-card">
                    <div class="card-header">
                      <el-icon><DataLine /></el-icon>
                      <span>Resource Optimization &amp; Cost Reduction</span>
                    </div>
                    <div class="scenario-list">
                      <div class="scenario-item" @click="sendQuery('Pull the last 7 days of CPU / memory / bandwidth metrics and give cost-saving advice')">Pull last 7 days of metrics and suggest cost savings</div>
                      <div class="scenario-item" @click="sendQuery('My server utilization is low. How can I save money?')">Low server utilization — how do I save money?</div>
                    </div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="scenario-card">
                    <div class="card-header">
                      <el-icon><Share /></el-icon>
                      <span>Promotion Campaigns</span>
                    </div>
                    <div class="scenario-list">
                      <div class="scenario-item" @click="sendQuery('I want to promote ECS cloud servers. Do you have a poster?')">I want to promote ECS — do you have a poster?</div>
                      <div class="scenario-item" @click="sendQuery('Generate a promotional poster for the c7 compute-optimized family')">Generate a promotional poster for the c7 family</div>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </div>

          <div 
            v-for="(msg, index) in messages" 
            :key="index"
            :class="['message-row', msg.role]"
          >
            <div :class="['msg-avatar', msg.role === 'user' ? 'user-avatar' : 'ai-avatar']">
              {{ msg.role === 'user' ? 'U' : 'AI' }}
            </div>
            <div class="message-bubble" v-html="renderMarkdown(msg.content)"></div>
          </div>
          
          <div v-if="isLoading" class="message-row assistant">
             <div class="msg-avatar ai-avatar">AI</div>
             <div class="message-bubble loading">
               <el-icon class="is-loading"><Loading /></el-icon> Thinking and invoking tools...
             </div>
          </div>
        </div>

        <div class="input-area">
          <el-input
            v-model="inputQuery"
            type="textarea"
            :rows="3"
            placeholder="Type your question. Shift + Enter for newline, Enter to send."
            @keydown.enter.prevent="handleEnter"
            :disabled="isLoading"
          />
          <el-button
            type="primary"
            class="send-btn"
            :icon="Position"
            :loading="isLoading"
            @click="sendQuery(inputQuery)"
            :disabled="!inputQuery.trim()"
          >
            Send
          </el-button>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { Plus, ChatDotRound, Service, Position, Loading, Monitor, List, DataLine, Share } from '@element-plus/icons-vue'
import { marked } from 'marked'

// Local component state
const inputQuery = ref('')
const isLoading = ref(false)
const messageListRef = ref<HTMLElement | null>(null)
const currentSessionId = ref('session_default_1')

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([])

const sessions = ref([
  { id: 'session_default_1', name: 'New chat' }
])

// Init
onMounted(() => {
  // (Could restore sessions / messages from localStorage here.)
})

const createNewSession = () => {
  const newId = `session_${Date.now()}`
  sessions.value.unshift({ id: newId, name: 'New chat' })
  currentSessionId.value = newId
  messages.value = []
}

const switchSession = (id: string) => {
  if (currentSessionId.value === id) return
  currentSessionId.value = id
  messages.value = [] // TODO: fetch this session's history from local storage or backend
}

const renderMarkdown = (text: string) => {
  return marked(text)
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

const handleEnter = (e: KeyboardEvent) => {
  if (e.shiftKey) return
  if (inputQuery.value.trim() && !isLoading.value) {
    sendQuery(inputQuery.value)
  }
}

const sendQuery = async (query: string) => {
  if (!query.trim()) return
  
  const text = query.trim()
  inputQuery.value = ''

  // Append the user message
  messages.value.push({ role: 'user', content: text })
  scrollToBottom()

  isLoading.value = true

  // Pre-create an empty assistant message that will accumulate the streamed chunks
  const assistantMessage: Message = { role: 'assistant', content: '' }
  messages.value.push(assistantMessage)
  const currentMsgIndex = messages.value.length - 1

  try {
    // Call the FastAPI backend and consume the SSE stream
    const response = await fetch('http://127.0.0.1:8090/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: text,
        user_id: 'user_1001',
        session_id: currentSessionId.value
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder('utf-8')
    isLoading.value = false // streaming has started; turn off the loading indicator

    if (reader) {
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // keep the trailing partial line for the next iteration

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim()
            if (dataStr === '[DONE]') continue
            if (!dataStr) continue

            try {
              const data = JSON.parse(dataStr)
              if (data.content && messages.value[currentMsgIndex]) {
                messages.value[currentMsgIndex].content += data.content
                scrollToBottom()
              }
              if (data.done) {
                // Stream finished
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e, dataStr)
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('API Error:', error)
    if (messages.value[currentMsgIndex]) {
      messages.value[currentMsgIndex].content = '❌ Request failed. Make sure the backend is running (FastAPI on port 8090).'
    }
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-container {
  height: 100vh;
  width: 100vw;
  background: radial-gradient(circle at 10% 20%, #e6f0ff 0%, #eef5ff 35%, #f6f8fc 100%);
  overflow: hidden;
  padding: 16px;
  box-sizing: border-box;
}
.app-shell {
  height: 100%;
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid #e7ebf3;
  box-shadow: 0 20px 50px rgba(15, 35, 95, 0.08);
  background: #fff;
}
.sidebar {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 18px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-logo {
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #60a5fa, #2563eb);
}
.sidebar-header h2 {
  margin: 0;
  font-size: 16px;
  color: #f8fafc;
  letter-spacing: 0.4px;
}
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.session-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #dbeafe;
  transition: all 0.3s;
  border: 1px solid transparent;
}
.session-item:hover {
  background-color: rgba(96, 165, 250, 0.18);
}
.session-item.active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.24), rgba(37, 99, 235, 0.22));
  color: #eff6ff;
  font-weight: 500;
  border-color: rgba(96, 165, 250, 0.35);
}
.user-info {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  gap: 10px;
}
.username {
  font-weight: 600;
  color: #e2e8f0;
}

.chat-main {
  display: flex;
  flex-direction: column;
  padding: 0;
  background: linear-gradient(180deg, #f8fbff 0%, #f6f8fc 100%);
}
.chat-header {
  padding: 16px 28px 12px;
  border-bottom: 1px solid #e7edf7;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
}
.header-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}
.header-subtitle {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  scroll-behavior: smooth;
}
.empty-state {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #64748b;
  background: #ffffff;
  border: 1px solid #e7edf7;
  border-radius: 16px;
  padding: 40px;
}
.welcome-title {
  margin-top: 16px;
  margin-bottom: 8px;
  color: #1e293b;
  font-size: 24px;
  font-weight: 600;
}
.welcome-desc {
  margin-bottom: 32px;
  color: #64748b;
  font-size: 15px;
}
.scenario-container {
  width: 100%;
  max-width: 800px;
}
.scenario-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  height: 100%;
  transition: all 0.3s ease;
}
.scenario-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border-color: #cbd5e1;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 16px;
}
.card-header .el-icon {
  color: #3b82f6;
  font-size: 20px;
}
.scenario-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.scenario-item {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 14px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
}
.scenario-item:hover {
  background: #eff6ff;
  border-color: #93c5fd;
  color: #2563eb;
  transform: translateY(-2px);
}

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
  max-width: 86%;
  align-items: flex-start;
}
.message-row.user {
  flex-direction: row-reverse;
  margin-left: auto;
}
.msg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.user-avatar {
  color: #eff6ff;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
}
.ai-avatar {
  color: #f8fafc;
  background: linear-gradient(135deg, #0ea5e9, #22c55e);
}
.mini-avatar {
  width: 28px;
  height: 28px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
}
.message-bubble {
  background: #ffffff;
  padding: 13px 16px;
  border-radius: 14px;
  border: 1px solid #e7edf7;
  box-shadow: 0 8px 24px rgba(15, 35, 95, 0.05);
  line-height: 1.6;
  color: #1e293b;
  font-size: 15px;
}
.message-row.user .message-bubble {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #ffffff;
  border-color: rgba(59, 130, 246, 0.35);
}
.message-row.assistant .message-bubble {
  border-top-left-radius: 0;
}
.message-row.user .message-bubble {
  border-top-right-radius: 0;
}
.message-bubble :deep(p) { margin: 0 0 10px 0; }
.message-bubble :deep(p:last-child) { margin: 0; }
.message-bubble :deep(img) { max-width: 100%; border-radius: 8px; margin-top: 10px; }
.message-bubble :deep(pre) { background: #f4f4f5; padding: 10px; border-radius: 6px; overflow-x: auto; }
.message-bubble :deep(code) { font-family: monospace; }

.input-area {
  padding: 16px 28px 20px;
  background: #ffffff;
  border-top: 1px solid #e7edf7;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.send-btn {
  align-self: flex-end;
  width: 110px;
  border-radius: 10px;
}
</style>
