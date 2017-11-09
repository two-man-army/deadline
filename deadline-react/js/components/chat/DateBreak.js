import React from 'react'
import PropTypes from 'prop-types'

const DateBreak = ({date}) => (
  <div className='date-break'>
    <h4 className='date-break-heading'>{date}</h4>
  </div>
)

DateBreak.propTypes = {
  date: PropTypes.string.isRequired
}

export default DateBreak
