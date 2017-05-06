import axios from 'axios'
import Auth from './auth.js'
import {SweetAlertError} from './errors.js'
import {convertFromUrlToFriendlyText} from './helpers.js'

/**
 * Fills a config with headers of the required authentication for the backend
 * @return {Object} - A config to be used on an axios request
 */
function getAxiosConfig () {
  return {headers: {'Authorization': 'Token ' + (Auth.getToken() || '')}}
}

/**
 * Issues a POST request to the server, trying to log in the user.
 * Returns the unique user AuthToken, which is needed for further authentication
 * @param {String} email
 * @param {String} password
 */
function postLogIn (email, password) {
  return axios.post('http://localhost:8000/accounts/login/', {email, password}).then(resp => {
    let authToken = resp.data['user_token']
    Auth.authenticateUser(authToken)
    console.log(`Authenticated user with ${authToken}`)
  }).catch(err => {
    console.log(`Error while trying to log in: ${err}`)
  })
}

function postRegister (email, password, username) {
  return axios.post('http://localhost:8000/accounts/register/', {
    username, email, password
  }).then(resp => {
    let authToken = resp.data['user_token']
    Auth.authenticateUser(authToken)
    console.log(`Authenticated user (through register) with ${authToken}`)
  }).catch(err => {
    if (err.response && err.response.data) {
      if (err.response.data.email) {
        throw new SweetAlertError('Invalid e-mail', 'A user with that e-mail already exists!')
      }
    }
    throw err
  })
}

/**
 * Queries the server for all the Challenge Categories and returns them in the following way:
 * @returns {Object} [{"name": "Main Category",
 *                    "sub_categories": ["a", "b", "c"] }, .. and so on ]
 */
function getCategoriesMetaInfo () {
  return axios.get('http://localhost:8000/challenges/categories/all').then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while fetching categories: ${err}`)
    throw err
  })
}

function getLatestAttemptedChallenges () {
  return axios.get('http://localhost:8000/challenges/latest_attempted', getAxiosConfig()).then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while fetching latest attempted challenges: ${err}`)
    throw err
  })
}

/**
 * Returns meta information about challenges from a specific SubCategory
 */
function getSubCategoryChallenges (subCategory) {
  // TODO: Fix back-end to work with url friendly text subcategory query
  let subCategoryStr = convertFromUrlToFriendlyText(subCategory)
  return axios.get(`http://localhost:8000/challenges/subcategories/${subCategoryStr}`, getAxiosConfig())
  .then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while fetching challenges from subcategory ${subCategoryStr}`)
    console.log(err)
    throw err
  })
}

/**
 * Returns information about a specific Challenge
 * @param {String} challengeId
 */
function getChallengeDetails (challengeId) {
  return axios.get(`http://localhost:8000/challenges/${challengeId}`, getAxiosConfig())
  .then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while fetching Challenge with ID ${challengeId}`)
    throw err
  })
}

export { postLogIn, postRegister, getCategoriesMetaInfo, getAxiosConfig, getLatestAttemptedChallenges, getSubCategoryChallenges, getChallengeDetails }
