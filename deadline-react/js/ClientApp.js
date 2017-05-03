import React from 'react'
import PropTypes from 'prop-types'
import { render } from 'react-dom'
import Sidebar from './Sidebar.js'
import LoginPage from './LoginPage.js'
import Auth from './auth.js'
const selector = document.getElementById('app')

let App = null
if (Auth.isUserAuthenticated()) {
  App = (props) => {
    return (
      <div className='app'>
        <Sidebar />
      </div>
    )
  }
} else {
  App = (props) => {
    return (
      <div className='app'>
        <LoginPage />
      </div>
    )
  }
}

App.propTypes = {
  name: PropTypes.string
}

render(<App name='deadline' />, selector)
