import React from 'react'
import PropTypes from 'prop-types'

const Level = ({className}) => (
  <span className={`${className || 'lvl'}`}>Lvl: 140</span>
)

Level.propTypes = {
  className: PropTypes.string
}

export default Level
