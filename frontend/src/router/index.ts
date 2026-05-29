/**
 * Vue Router 路由配置
 * 
 * meta 字段说明：
 * - requiresAuth: 是否需要登录
 * - roles: 允许访问的角色列表
 * - title: 页面标题
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore, type UserRole } from '@/stores/user'

/**
 * 扩展 vue-router 的 RouteMeta 接口
 * 为路由 meta 字段添加类型支持
 */
declare module 'vue-router' {
  interface RouteMeta {
    /** 页面标题 */
    title?: string
    /** 是否需要登录 */
    requiresAuth?: boolean
    /** 允许访问的角色列表 */
    roles?: UserRole[]
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/textbook/:id',
    name: 'TextbookReader',
    component: () => import('@/views/TextbookReader.vue'),
    meta: { title: '教材阅读' }
  },
  {
    path: '/textbook/:id/chapter/:chapterId',
    name: 'ChapterReader',
    component: () => import('@/views/TextbookReader.vue'),
    meta: { title: '章节阅读' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue'),
    meta: { title: '修改密码' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册' }
  },
  {
    path: '/change-password',
    name: 'ChangePassword',
    component: () => import('@/views/ChangePassword.vue'),
    meta: { requiresAuth: true, title: '修改密码' }
  },
  {
    path: '/admin',
    name: 'AdminLayout',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { 
      requiresAuth: true, 
      roles: ['super_admin', 'admin', 'editor'],
      title: '管理后台' 
    },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { 
          requiresAuth: true, 
          roles: ['super_admin', 'admin'],
          title: '概览' 
        }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/admin/Users.vue'),
        meta: { 
          requiresAuth: true, 
          roles: ['super_admin', 'admin'],
          title: '用户管理' 
        }
      },
      {
        path: 'permissions',
        name: 'PermissionManager',
        redirect: '/admin/users'
      },
      {
        path: 'textbooks',
        name: 'Textbooks',
        component: () => import('@/views/admin/Textbooks.vue'),
        meta: { 
          requiresAuth: true, 
          roles: ['super_admin', 'admin', 'editor'],
          title: '教材管理' 
        }
      },
      {
        path: 'textbooks/:id',
        name: 'ContentManager',
        component: () => import('@/views/admin/ContentManager.vue'),
        meta: { 
          requiresAuth: true, 
          roles: ['super_admin', 'admin', 'editor'],
          title: '内容管理' 
        }
      },
      {
        path: 'textbooks/:id/edit/:chapterId',
        name: 'Editor',
        component: () => import('@/views/admin/Editor.vue'),
        meta: { 
          requiresAuth: true, 
          roles: ['super_admin', 'admin', 'editor'],
          title: '页面编辑' 
        }
      },
      {
        path: 'textbooks/:id/history/:chapterId',
        name: 'VersionHistory',
        component: () => import('@/views/admin/VersionHistory.vue'),
        meta: { 
          requiresAuth: true, 
          roles: ['super_admin', 'admin', 'editor'],
          title: '版本历史' 
        }
      },
      {
        path: 'media',
        name: 'MediaLibrary',
        component: () => import('@/views/admin/MediaLibrary.vue'),
        meta: { 
          requiresAuth: true, 
          roles: ['super_admin', 'admin', 'editor'],
          title: '媒体库' 
        }
      }
    ]
  },
  {
    path: '/search',
    name: 'SearchResults',
    component: () => import('@/views/SearchResults.vue'),
    meta: { title: '搜索结果' }
  },
  {
    path: '/setup',
    name: 'SetupWizard',
    component: () => import('@/views/SetupWizard.vue'),
    meta: { title: '系统初始化' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * 全局前置路由守卫
 * 处理登录验证和角色权限检查
 */
router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()
  
  // 初始化状态检查（跳过设置页和登录页本身）
  if (to.path !== '/setup' && to.path !== '/login') {
    try {
      const { getSetupStatus } = await import('@/api/setup')
      const status = await getSetupStatus()
      if (!status.initialized) {
        next('/setup')
        return
      }
    } catch {
      // API 调用失败时跳转到设置页
      next('/setup')
      return
    }
  }
  
  // 如果系统已初始化且用户访问 /setup，跳转到登录页
  if (to.path === '/setup') {
    try {
      const { getSetupStatus } = await import('@/api/setup')
      const status = await getSetupStatus()
      if (status.initialized) {
        next('/login')
        return
      }
    } catch {
      // 检查失败时允许停留在设置页
    }
  }
  
  document.title = to.meta.title ? `${to.meta.title} - ROS小车教学` : 'ROS小车教学'
  
  // 需要登录但未登录，跳转到登录页并携带 redirect 参数
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }
  
  // 角色权限检查：当前角色不在允许列表中时跳转首页
  if (to.meta.roles?.length && !to.meta.roles.includes(userStore.role)) {
    // editor 访问 /admin 时重定向到教材管理（因为 Dashboard 不允许 editor 访问）
    if (to.path === '/admin' && userStore.role === 'editor') {
      next('/admin/textbooks')
      return
    }
    next('/')
    return
  }
  
  // 必须修改密码检查：阻止访问除 /change-password 外的页面
  if (userStore.userInfo?.must_change_password && to.path !== '/change-password') {
    next('/change-password')
    return
  }
  
  next()
})

export default router
