import { bus } from '@/main'
import { UserManager } from 'oidc-client-ts'

let manager = null

const authInterface = {
  validateAccess: function (to, from, next) {
    manager.getUser().then(user => {
      if (user && !user.expired) {
        next()
      } else {
        localStorage.clear()
        if (to.name !== 'Login') {
          sessionStorage.setItem('next', to.name)
          sessionStorage.setItem('nextParams', JSON.stringify(to.params))
        }
        manager.signinRedirect()
      }
    })
  },
  oauthLoginCallback: function () {
    return manager.signinRedirectCallback().then(() => {
      bus.$emit('userSignedIn')
    })
  },
  clear: function () {
    manager.clearStaleState()
  },
  getAccessToken: function () {
    return manager.getUser().then(user => {
      if (!user) {
        return null
      }
      return user.access_token
    })
  },
  getUserInfo: function () {
    return manager.getUser()
      .then(user => {
        if (!user || user.expired) {
          return null
        }
        const parts = user.id_token.split('.')
        const payload = decodeURIComponent(
          escape(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
        )
        return JSON.parse(payload)
      })
  },
  oauthLogout: async function () {
    return manager.signoutRedirect()
  }
}

export default {
  async install (Vue, options) {
    manager = new UserManager({
      authority: Vue.prototype.$config.AUTH_AUTHORITY,
      client_id: Vue.prototype.$config.AUTH_CLIENT_ID,
      redirect_uri: location.origin + '/oauth-callback',
      response_type: 'code',
      response_mode: 'fragment',
      post_logout_redirect_uri: location.origin,
      scope: `openid profile email offline_access api://${Vue.prototype.$config.AUTH_APP_ID}/API.call`
    })
    Vue.prototype.$auth = authInterface
  }
}
