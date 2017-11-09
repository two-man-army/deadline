import React from 'react'
import PropTypes from 'prop-types'
import UserImage from '../UserImage'
import DateBreak from './DateBreak'
import ChatUserMsg from './ChatUserMsg'

const ChatFriendMsg = ({date, path, msg}) => (
  <div className='chat-friend-msg'>
    <DateBreak date={date} />
    <div className='msg-wrapper'>
      <UserImage path={path} />
      <ChatUserMsg msg={msg} />
    </div>
  </div>
)

ChatFriendMsg.propTypes = {
  date: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired,
  msg: PropTypes.string.isRequired

}

export default ChatFriendMsg
