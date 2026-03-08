/**
 * Vue Router Configuration
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/auth/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/auth/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/auth/register/confirm/:token',
    name: 'RegisterConfirm',
    component: () => import('@/views/auth/RegisterConfirm.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/auth/password-reset',
    name: 'PasswordReset',
    component: () => import('@/views/auth/PasswordReset.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/auth/password-reset/confirm/:token',
    name: 'PasswordResetConfirm',
    component: () => import('@/views/auth/PasswordResetConfirm.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/user/profile',
    name: 'UserProfile',
    component: () => import('@/views/user/Profile.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/users',
    name: 'UserManagement',
    component: () => import('@/views/admin/UserManagement.vue'),
    meta: { requiresAuth: true, requiresRole: ['admin', 'support'] },
  },
  {
    path: '/admin/roles',
    name: 'RoleManagement',
    component: () => import('@/views/admin/RoleManagement.vue'),
    meta: { requiresAuth: true, requiresRole: ['admin'] },
  },
  {
    path: '/admin/data-maintenance',
    name: 'DataMaintenance',
    component: () => import('@/views/admin/DataMaintenance.vue'),
    meta: { requiresAuth: true, requiresRole: ['admin', 'support'] },
  },
  {
    path: '/records',
    name: 'RecordList',
    component: () => import('@/views/records/RecordList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/records/new',
    name: 'RecordCreate',
    component: () => import('@/views/records/RecordForm.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/records/:id',
    name: 'RecordEdit',
    component: () => import('@/views/records/RecordForm.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/records/:recordId/pages',
    name: 'PageList',
    component: () => import('@/views/records/PageList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/records/:recordId/pages-gallery',
    name: 'RecordPagesGallery',
    component: () => import('@/views/records/RecordPagesGallery.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/records/:recordId/pages/new',
    name: 'PageCreate',
    component: () => import('@/views/records/PageForm.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/records/:recordId/pages/:pageId',
    name: 'PageDetail',
    component: () => import('@/views/records/PageDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/records/:recordId/pages/:pageId/viewer',
    name: 'PageViewer',
    component: () => import('@/views/records/PageViewer.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/records/:recordId/pages/:pageId/edit',
    name: 'PageEdit',
    component: () => import('@/views/records/PageForm.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/api-docs',
    name: 'ApiDocs',
    component: () => import('@/views/ApiDocs.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/About.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/imprint',
    name: 'Imprint',
    component: () => import('@/views/Imprint.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/data-protection',
    name: 'DataProtection',
    component: () => import('@/views/DataProtection.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const requiresRole = to.meta.requiresRole

  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  if (requiresRole && !requiresRole.some((role) => authStore.hasRole(role))) {
    next({ name: 'Home' })
    return
  }

  next()
})

export default router
