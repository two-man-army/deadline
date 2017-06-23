import axios from 'axios'
import Auth from './auth.js'
import {SweetAlertError, EmptySolutionError} from './errors.js'
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
    let userName = resp.data['username']
    Auth.authenticateUser(authToken, userName)
    console.log(`Authenticated user with ${authToken}`)
  }).catch(err => {
    console.log(`Error while trying to log in: ${err}`)
    if (err.response && err.response.data && err.response.data.error) {
      if (err.response.data.error.toLowerCase().includes('invalid credentials')) {
        throw new SweetAlertError('Invalid Credentials', 'Your e-mail or password is invalid!')
      }
    }
  })
}

function postRegister (email, password, username) {
  return axios.post('http://localhost:8000/accounts/register/', {
    username, email, password
  }).then(resp => {
    let authToken = resp.data['user_token']
    let userName = resp.data['username']
    Auth.authenticateUser(authToken, userName)
    console.log(`Authenticated user (through register) with ${authToken}`)
  }).catch(err => {
    if (err.response && err.response.data) {
      if (err.response.data.email) {
        throw new SweetAlertError('Invalid e-mail', 'A user with that e-mail already exists!', 'email')
      } else if (err.response.data.username) {
        throw new SweetAlertError('Invalid Username', 'A user with that username already exists!', 'username')
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

/**
 * Posts the code as the solution to a specific Challenge
 * @param {Number} challengeId
 * @param {String} code
 */
function postChallengeSolution (challengeId, code, language) {
  return axios.post(`http://localhost:8000/challenges/${challengeId}/submissions/new`, {code, language}, getAxiosConfig())
  .then(resp => {
    let submission = resp.data
    return submission
  }).catch(err => {
    if (err.response && err.response.data) {
      throw new EmptySolutionError('Error: ', err.response.data.error)
    }
    console.log(`Err while submitting solution to challenge with ID ${challengeId}`)
    throw err
  })
}

/**
 * Queries the server for a specific solution
 * @param {Number} challengeId
 * @param {Number} solutionId
 */
function getChallengeSolution (challengeId, solutionId) {
  return axios.get(`http://localhost:8000/challenges/${challengeId}/submissions/${solutionId}`, getAxiosConfig()).then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while getting solution ${solutionId} for challenge ${challengeId}`)
    throw err
  })
}

/**
 * Queries the server for the test cases of a given solution
 * @param {Number} challengeId
 * @param {Number} solutionId
 */
function getSolutionTests (challengeId, solutionId) {
  return axios.get(`http://localhost:8000/challenges/${challengeId}/submissions/${solutionId}/tests`, getAxiosConfig()).then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while getting tests for solution ${solutionId} for challenge ${challengeId}`)
    throw err
  })
}

/**
 * Queries the server for all the submissions for a challenge from the current user
 * @param {Number} challengeId
 */
function getAllUserSolutions (challengeId) {
  return axios.get(`http://localhost:8000/challenges/${challengeId}/submissions/all`, getAxiosConfig()).then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while fetching solutions for challenge ${challengeId}`)
    throw err
  })
}

/**
 * Queries the server for the top submissions for a challenge (one for each author)
 * @param {Number} challengeId
 */
function getTopSolutions (challengeId) {
  return axios.get(`http://localhost:8000/challenges/${challengeId}/submissions/top`, getAxiosConfig()).then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while fetching top solutions for challenge ${challengeId}`)
    throw err
  })
}

/**
 * Queries the server for a Language object by its name
 * @param {Name} langName
 */
function getLanguageDetail (langName) {
  return axios.get(`http://localhost:8000/challenges/languages/${langName}`, getAxiosConfig()).then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while fetching language details for language ${langName}`)
    throw err
  })
}

/**
 * Queries the server for the current user's best submission for the given challenge
 * @param {Number} challengeId
 */
function getSelfUserTopSubmission (challengeId) {
  return axios.get(`http://localhost:8000/challenges/${challengeId}/submissions/selfTop`, getAxiosConfig()).then(resp => {
    return resp.data
  }).catch(err => {
    if (err.response.statusCode === 404) {
      return {}
    }
    console.log(`Error while fetching the current user's top submission for challenge ${challengeId}`)
    throw err
  })
}

/**
 * Issues a post request to the server from the name of the user, casting a vote on a submissoin
 * @param {Number} submissionId - the ID of the submission
 * @param {Boolean} isUpvote - boolean indicating if the vote is an upvote
 */
function postCastSubmissionVote (submissionId, isUpvote) {
  return axios.post(`http://localhost:8000/challenges/submissions/${submissionId}/vote`, {'is_upvote': isUpvote}, getAxiosConfig()).then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while voting for submission ${submissionId}!`)
    throw err
  })
}

/**
 * Issues a delete request to the server from the name of the user, removing his vote on a submission
 * @param {Number} submissionId - the ID of the submission
 */
function deleteRemoveSubmissionVote (submissionId) {
  return axios.delete(`http://localhost:8000/challenges/submissions/${submissionId}/removeVote`, getAxiosConfig()).then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while voting for submission ${submissionId}!`)
    throw err
  })
}

/**
 *  Issues a GET request to get the overall leaderboard, containing every user ordered by their score
 */
function getOverallLeaderboard () {
  return axios.get('http://localhost:8000/challenges/getLeaderboard', getAxiosConfig()).then(resp => {
    return resp.data
  }).catch(err => {
    console.log(`Error while GETting the overall leaderboard`)
    throw err
  })
}

export {getAxiosConfig,
  postLogIn, postRegister, postChallengeSolution, postCastSubmissionVote,
  getLatestAttemptedChallenges, getSubCategoryChallenges, getChallengeDetails, getCategoriesMetaInfo,
  getTopSolutions, getAllUserSolutions, getChallengeSolution, getSolutionTests, getSelfUserTopSubmission,
  getOverallLeaderboard, getLanguageDetail,
  deleteRemoveSubmissionVote
}
