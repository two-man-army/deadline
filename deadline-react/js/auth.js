const ID_TOKEN_KEY = 'authToken'
const USERNAME_KEY = 'username'

class Auth {
  /**
   * Authenticate a user. Save a token string in Local Storage
   *
   * @param {string} token
   */

  static authenticateUser (token, userName) {
    if (window.localStorage) {
      window.localStorage.setItem(ID_TOKEN_KEY, token)
      window.localStorage.setItem(USERNAME_KEY, userName)
    }
  }

  /**
   * Check if a user is authenticated - check if a token is saved in Local Storage
   *
   * @returns {boolean}
   */
  static isUserAuthenticated () {
    if (window.localStorage) {
      return window.localStorage.getItem(ID_TOKEN_KEY) !== null
    }
  }

  /**
   * Deauthenticate a user. Remove a token from Local Storage.
   *
   */
  static deauthenticateUser () {
    if (window.localStorage) {
      window.localStorage.removeItem(ID_TOKEN_KEY)
      window.localStorage.removeItem(USERNAME_KEY)
    }
  }

  /**
   * Get a token value.
   *
   * @returns {string}
   */
  static getToken () {
    if (window.localStorage) {
      return window.localStorage.getItem(ID_TOKEN_KEY)
    }
  }

  /**
   * Gets the current user's username
   *
   * @returns {string}
   */
  static getCurrentUserUsername () {
    if (window.localStorage) {
      return window.localStorage.getItem(USERNAME_KEY)
    }
  }
}

export default Auth
