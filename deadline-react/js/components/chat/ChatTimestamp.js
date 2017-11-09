import React from 'react'
import PropTypes from 'prop-types'

const ChatTimestamp = ({time}) => (
  <span className='time-stamp'>{time}</span>
)

ChatTimestamp.propTypes = {
  time: PropTypes.string.isRequired
}

export default ChatTimestamp
