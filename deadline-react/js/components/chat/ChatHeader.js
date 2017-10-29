import React from 'react'
import PropTypes from 'prop-types'

const ChatHeader = ({heading}) => (
  <div className='chat-header'>{heading}</div>
)

ChatHeader.propTypes = {
  heading: PropTypes.string.isRequired
}

export default ChatHeader
