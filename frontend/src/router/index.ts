import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: () => import('../components/Layout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('../views/HomeView.vue')
        },
        {
          path: 'music',
          name: 'music',
          component: () => import('../views/MusicView.vue')
        },
        {
          path: 'tagging-question',
          name: 'tagging-question',
          component: () => import('../views/TaggingQuestionView.vue')
        },
        {
          path: 'tagging-task',
          name: 'tagging-task',
          component: () => import('../views/TaggingTaskView.vue')
        },
        {
          path: 'user',
          name: 'user',
          component: () => import('../views/UserView.vue')
        }
      ]
    }
  ]
})

// 路由守卫：检查登录状态
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 如果访问需要登录的页面但未登录，跳转到登录页
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } 
  // 如果已登录访问登录页，跳转到首页
  else if (to.path === '/login' && userStore.isLoggedIn) {
    next('/')
  } 
  // 其他情况正常导航
  else {
    next()
  }
})

export default router
