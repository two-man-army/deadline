import React from 'react'
import PropTypes from 'prop-types'

const UserImage = ({path}) => (
  <img src={path} alt='' />
)

UserImage.propTypes = {
  path: PropTypes.string.isRequired
}

export default UserImage
