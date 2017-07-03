import React from 'react'
import { render } from 'react-dom'
// import Sidebar from './Sidebar.js'
// import SideBarNav from './components/SideBarNav'
import LoginPage from './LoginPage.js'
import Dashboard from './Dashboard.js'
import {HashRouter as Router} from 'react-router-dom'
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider'
import getMuiTheme from 'material-ui/styles/getMuiTheme'
import {orange600} from 'material-ui/styles/colors'

const selector = document.getElementById('app')

// Configure the colors for Mui components
const muiTheme = getMuiTheme({
  palette: {
    textColor: orange600,
    accent1Color: '#ff4081'
  }
})

const AuthenticatedApp = (props) => {
  return (
    <Dashboard />
  )
}

render(
  (
    <MuiThemeProvider muiTheme={muiTheme}>
      <Router>
        <LoginPage authApp={AuthenticatedApp} />
      </Router>
    </MuiThemeProvider>
  )
, selector)
