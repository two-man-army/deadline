import React from 'react'
import PropTypes from 'prop-types'

const Username = ({name}) => (
  <h3>{name}</h3>
)

Username.propTypes = {
  name: PropTypes.string.isRequired
}

export default Username
