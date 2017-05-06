import React from 'react'
import PropTypes from 'prop-types'
import { render } from 'react-dom'
import Sidebar from './Sidebar.js'
import LoginPage from './LoginPage.js'
import Auth from './auth.js'
import Dashboard from './Dashboard.js'
import {HashRouter as Router} from 'react-router-dom'
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider'
import getMuiTheme from 'material-ui/styles/getMuiTheme'
import {orange600} from 'material-ui/styles/colors'

const selector = document.getElementById('app')

// Configure the colors for Mui components
const muiTheme = getMuiTheme({
  palette: {
    textColor: orange600
  }
})

let App = null
if (Auth.isUserAuthenticated()) {
  App = (props) => {
    return (
      <div className='app'>
        <Sidebar />
        <Dashboard />
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

render(
  (
    <MuiThemeProvider muiTheme={muiTheme}>
      <Router>
        <App name='deadline' />
      </Router>
    </MuiThemeProvider>
  )
, selector)
