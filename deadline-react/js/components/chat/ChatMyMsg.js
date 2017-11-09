import React from 'react'
import PropTypes from 'prop-types'
import ChatUserMsg from './ChatUserMsg'

const ChatMyMsg = ({msg}) => (
  <div className='chat-my-msg'>
    <ChatUserMsg msg={msg} />
  </div>
)

ChatMyMsg.propTypes = {
  msg: PropTypes.string.isRequired
}

export default ChatMyMsg
