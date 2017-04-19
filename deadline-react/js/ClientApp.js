import React from 'react'
import PropTypes from 'prop-types'
import { render } from 'react-dom'

const selector = document.getElementById('app')

const App = (props) => {
  return (
    <div className='app'>
      <div className='landing'>
        <div>Hello0, {props.name}!</div>
      </div>
    </div>
  )
}

App.propTypes = {
  name: PropTypes.string
}

render(<App name='c0re' />, selector)
