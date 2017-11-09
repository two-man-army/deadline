import React from 'react'
import UserImage from '../UserImage'
import Username from '../Username'
import ChatTimestamp from './ChatTimestamp'
import ChatUserMsg from './ChatUserMsg'
import PropTypes from 'prop-types'

const ChatThreadListRow = ({name, path, msg, time}) => (
  <li className='chat-threadlist '>
    <UserImage path={path} />
    <div className='chat-member-wrapper'>
      <div className='chat-member-title'>
        <Username name={name} />
        <ChatTimestamp time={time} />
      </div>
      <ChatUserMsg msg={msg} />
    </div>
  </li>
)

ChatThreadListRow.propTypes = {
  name: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired,
  msg: PropTypes.string.isRequired,
  time: PropTypes.string.isRequired
}

export default ChatThreadListRow
