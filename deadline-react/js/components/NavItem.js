import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'

const NavItem = ({name, path, url}) => (
  <li className='nav-item'>
    <Link to={{pathname: url}}>
      <img src={path} alt='' />
      <span className='nav-item-text'>{name}</span>
    </Link>
  </li>
)

NavItem.propTypes = {
  name: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired
}

export default NavItem
