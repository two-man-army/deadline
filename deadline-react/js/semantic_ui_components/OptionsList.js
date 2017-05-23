import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'

const OptionsList = ({onClick}) => (
  <div className='account-options'>
    <ul>
      <li><Link to='/accounts/password/change/' onClick={onClick}>Change Password</Link></li>
      <li><Link to='/accounts/edit/' onClick={onClick}>Edit Profile</Link></li>
      <li><Link to='/accounts/something'>Something else</Link></li>
      <li><Link to='/accounts/logout/'>Logout</Link></li>
      <li><Link to='/accounts/else'>Something else</Link></li>
    </ul>
  </div>
)

OptionsList.propTypes = {
  onClick: PropTypes.func.isRequired
}

export default OptionsList
