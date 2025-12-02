import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import GraphView from '../views/GraphView.vue'
import WelcomeView from '@/views/WelcomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'welcome',
      component: WelcomeView
    },
    {
      path: '/chat/:storyId',
      name: 'chat',
      component: ChatView,
      props: true
    },
    {
      path: '/graph',
      name: 'graph',
      component: GraphView
    }
  ]
})

export default router
