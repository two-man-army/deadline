import React from 'react'
import UserImage from '../UserImage'
import Username from '../Username'
import PropTypes from 'prop-types'

const ChatThreadListRow = ({name, path, msg}) => (
  <ul className='chat-member'>
    <li className='chat-member-list'>
      <UserImage path={path} />
      <div className='chat-member-wrapper'>
        <Username name={name} />
        <p>{msg}</p>
      </div>
    </li>
  </ul>
)

ChatThreadListRow.propTypes = {
  name: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired,
  msg: PropTypes.string.isRequired
}

export default ChatThreadListRow
