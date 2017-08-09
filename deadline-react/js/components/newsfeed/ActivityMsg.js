import React from 'react'
import PropTypes from 'prop-types'

const ActivityMsg = ({msg}) => (
  <span className='activity-msg'>{msg}</span>
)

ActivityMsg.propTypes = {
  msg: PropTypes.string.isRequired
}

export default ActivityMsg
