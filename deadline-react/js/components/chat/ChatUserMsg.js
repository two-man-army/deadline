import React from 'react'
import PropTypes from 'prop-types'

const ChatUserMsg = ({msg}) => (
  <p>{msg}</p>
)

ChatUserMsg.propTypes = {
  msg: PropTypes.string.isRequired
}

export default ChatUserMsg
