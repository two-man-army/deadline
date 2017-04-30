import React from 'react'
import PropTypes from 'prop-types'
import { render } from 'react-dom'
import LoginPage from './LoginPage'

const selector = document.getElementById('app')

const App = (props) => {
  return (
    <div className='app'>
      <LoginPage />
    </div>
  )
}

App.propTypes = {
  name: PropTypes.string
}

render(<App name='deadline' />, selector)
