import React from 'react'
import PropTypes from 'prop-types'
import Level from './Level'
import Username from './Username'
import UserImage from './UserImage'

const NavProfile = ({name, path}) => (
  <section className='nav-profile'>
    <figure>
      <UserImage path={path} />
      <figcaption>
        <Username name={name} />
        <Level />
      </figcaption>
    </figure>
  </section>
)

NavProfile.propTypes = {
  name: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired
}

export default NavProfile
