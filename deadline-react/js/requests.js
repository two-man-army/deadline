import axios from 'axios'

function postLogIn (email, password) {
  return axios.post('http://localhost:8000/accounts/login/', {email, password}).then(resp => {
    return resp
  }).catch(err => {
    console.log(`Error while trying to log in: ${err}`)
  })
}

function postRegister (email, password, username) {
  return axios.post('http://localhost:8000/accounts/register/', {
    username, email, password
  }).then(resp => {
    console.log(resp)
  }).catch(err => {
    console.log(`Error while registering: ${err}`)
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

export { postLogIn, postRegister, getCategoriesMetaInfo }
