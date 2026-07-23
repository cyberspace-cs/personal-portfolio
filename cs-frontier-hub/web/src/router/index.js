import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Detail from '../views/Detail.vue'
import Favorites from '../views/Favorites.vue'
import Admin from '../views/Admin.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/item/:slug', name: 'detail', component: Detail, props: true },
    { path: '/favorites', name: 'favorites', component: Favorites },
    { path: '/admin', name: 'admin', component: Admin },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
