import React from 'react'
import { Link } from 'react-router-dom'

const OptionsList = () => (
  <div className='account-options'>
    <ul>
      <li><Link to='/accounts/password/change/'>Change Password</Link></li>
      <li><Link to='/accounts/edit/'>Edit Profile</Link></li>
      <li><Link to='/'>Something else</Link></li>
      <li><Link to='/accounts/logout/'>Logout</Link></li>
      <li><Link to='/'>Something else</Link></li>
    </ul>
  </div>
)

export default OptionsList
