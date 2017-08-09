import React from 'react'
import PropTypes from 'prop-types'
import TimeAgo from 'react-timeago'
import Username from '../Username'
import UserImage from '../UserImage'
import Level from '../Level'
import ActivityMsg from './ActivityMsg'

const Activity = ({name, path, msg, className}) => (
  <li className='activity-item'>
    <UserImage path={path} />
    <div className='activity-content'>
      <Username name={name} />
      <Level className='activity-item-lvl' />
      <ActivityMsg msg={msg} />
    </div>
    <div className='activity-timeago'>
      <TimeAgo date='Jun 30, 2017' />
    </div>
  </li>
)

Activity.propTypes = {
  name: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired,
  msg: PropTypes.string.isRequired,
  className: PropTypes.string
}

export default Activity
