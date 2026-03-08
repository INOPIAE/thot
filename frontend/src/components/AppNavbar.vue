<template>
  <nav class="app-navigation" :class="{ open: menuOpen }">
    <!-- Hamburger Toggle Button -->
    <button class="hamburger" @click="toggleMenu" aria-label="Toggle menu">
      <span></span>
      <span></span>
      <span></span>
    </button>

    <!-- Navigation Links -->
    <ul class="nav-list">
      <!-- Home -->
      <li><router-link to="/" @click="closeMenu">{{ t('nav.home') }}</router-link></li>

      <!-- Authentication Section -->
      <li v-if="!authStore.isAuthenticated" class="nav-section">
        <span class="nav-label">{{ t('nav.authentication') }}</span>
        <ul>
          <li><router-link to="/auth/login" @click="closeMenu">{{ t('nav.login') }}</router-link></li>
          <li><router-link to="/auth/register" @click="closeMenu">{{ t('nav.register') }}</router-link></li>
        </ul>
      </li>

      <!-- Records Section (Authenticated) -->
      <li v-if="authStore.isAuthenticated" class="nav-section">
        <span class="nav-label">{{ t('nav.records') }}</span>
        <ul>
          <li><router-link to="/records" @click="closeMenu">{{ t('nav.recordList') }}</router-link></li>
          <li><router-link to="/records/new" @click="closeMenu">{{ t('nav.createRecord') }}</router-link></li>
        </ul>
      </li>

      <!-- User Management Section (Authenticated) -->
      <li v-if="authStore.isAuthenticated" class="nav-section">
        <span class="nav-label">{{ t('nav.userManagement') }}</span>
        <ul>
          <li><router-link to="/user/profile" @click="closeMenu">{{ t('nav.myProfile') }}</router-link></li>
          <li v-if="authStore.hasRole('support') || authStore.hasRole('admin')">
            <router-link to="/admin/users" @click="closeMenu">{{ t('nav.adminUsers') }}</router-link>
          </li>
          <li><a href="#" @click.prevent="logout" class="logout-link">{{ t('nav.logout') }}</a></li>
        </ul>
      </li>

      <!-- Admin Section -->
      <li v-if="authStore.hasRole('support') || authStore.hasRole('admin')" class="nav-section">
        <span class="nav-label">{{ t('nav.administration') }}</span>
        <ul>
          <li v-if="authStore.hasRole('admin')">
            <router-link to="/admin/roles" @click="closeMenu">{{ t('nav.roles') }}</router-link>
          </li>
          <li><router-link to="/admin/data-maintenance" @click="closeMenu">{{ t('nav.dataMaintenance') }}</router-link></li>
        </ul>
      </li>

      <!-- Info Section -->
      <li class="nav-section">
        <span class="nav-label">{{ t('nav.information') }}</span>
        <ul>
          <li><router-link to="/api-docs" @click="closeMenu">{{ t('nav.apiDocumentation') }}</router-link></li>
          <li><router-link to="/about" @click="closeMenu">{{ t('nav.about') }}</router-link></li>
          <li><router-link to="/imprint" @click="closeMenu">{{ t('nav.imprint') }}</router-link></li>
          <li><router-link to="/data-protection" @click="closeMenu">{{ t('nav.dataProtection') }}</router-link></li>
        </ul>
      </li>
    </ul>
  </nav>
</template>

<script>
import { defineComponent } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

export default defineComponent({
  name: 'AppNavbar',
  setup() {
    const authStore = useAuthStore()
    const router = useRouter()
    const { t } = useI18n()

    return {
      authStore,
      router,
      t,
    }
  },
  data() {
    return {
      menuOpen: false,
    }
  },
  methods: {
    toggleMenu() {
      this.menuOpen = !this.menuOpen
    },
    closeMenu() {
      this.menuOpen = false
    },
    async logout() {
      await this.authStore.logout()
      this.closeMenu()
      this.$router.push('/auth/login')
    },
  },
})
</script>

<style scoped>
.app-navigation {
  width: 200px;
  background-color: #f9f9f9;
  border-right: 1px solid #ddd;
  padding: 0;
  position: relative;
}

.hamburger {
  display: none;
  flex-direction: column;
  background: none;
  border: none;
  cursor: pointer;
  padding: 1rem;
  gap: 0.4rem;
}

.hamburger span {
  width: 25px;
  height: 3px;
  background-color: #2c3e50;
  border-radius: 2px;
  transition: all 0.3s ease;
}

.nav-list {
  list-style: none;
  padding: 1rem 0;
  max-height: 100%;
  overflow-y: auto;
}

.nav-list > li {
  padding: 0;
}

.nav-list > li > a.router-link {
  display: block;
  padding: 0.75rem 1.5rem;
  color: #2c3e50;
  text-decoration: none;
  border-left: 4px solid transparent;
  transition: all 0.2s ease;
}

.nav-list > li > a:hover {
  background-color: #e8e8e8;
  border-left-color: #2c3e50;
}

.nav-list > li > a.router-link-active {
  background-color: #ddd;
  font-weight: 600;
  border-left-color: #2c3e50;
}

.nav-section {
  padding: 0.5rem 0;
  border-top: 1px solid #e0e0e0;
}

.nav-section:first-child {
  border-top: none;
}

.nav-label {
  display: block;
  padding: 0.75rem 1.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #666;
  letter-spacing: 0.5px;
}

.nav-section > ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-section > ul > li {
  padding: 0;
}

.nav-section > ul > li > a {
  display: block;
  padding: 0.5rem 2rem;
  color: #2c3e50;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  border-left: 4px solid transparent;
}

.nav-section > ul > li > a:hover {
  background-color: #e8e8e8;
  border-left-color: #2c3e50;
}

.nav-section > ul > li > a.router-link-active {
  background-color: #ddd;
  font-weight: 600;
  border-left-color: #2c3e50;
}

.logout-link {
  display: block;
  padding: 0.5rem 2rem;
  color: #e74c3c;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  border-left: 4px solid transparent;
}

.logout-link:hover {
  background-color: #ffebee;
  border-left-color: #e74c3c;
}

/* Tablet styles (768px - 1023px) */
@media (max-width: 1023px) {
  .app-navigation {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #ddd;
  }

  .hamburger {
    display: flex;
  }

  .nav-list {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
  }

  .app-navigation.open .nav-list {
    max-height: 1000px;
  }
}

/* Mobile styles (max 767px) */
@media (max-width: 767px) {
  .app-navigation {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #ddd;
  }

  .hamburger {
    display: flex;
  }

  .nav-list {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
    padding: 0;
  }

  .app-navigation.open .nav-list {
    max-height: 1000px;
    padding: 1rem 0;
  }

  .nav-list > li > a.router-link,
  .nav-section > ul > li > a {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .nav-label {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}
</style>
