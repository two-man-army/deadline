import React from 'react'
import PropTypes from 'prop-types'

const Button = ({text}) => (
  <div className='button-wrapper'>
    <button className='button-wrapper__button' type='submit' >{text}</button>
  </div>
)

Button.propTypes = {
  text: PropTypes.string.isRequired
}

export default Button
