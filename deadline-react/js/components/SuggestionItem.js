import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'
import UserImage from './UserImage'
import Username from './Username'
import Level from './Level'

const SuggestionItem = ({path, name}) => (
  <Link to=''>
    <li className='suggestion-item'>
      <UserImage path={path} />
      <div className='suggestion-content'>
        <Username name={name} />
        <Level className='suggestion-item-lvl' />
      </div>
      <img className='cancel-suggestion' src={'assets/img/sidebar/cancel.svg'} alt='' />
    </li>
  </Link>
)

SuggestionItem.propTypes = {
  name: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired
}

export default SuggestionItem
