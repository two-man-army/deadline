import React from 'react'
import PropTypes from 'prop-types'
import { Progress } from 'semantic-ui-react'

// TODO: Add different colors in regards to percentage
const ProgressBar = ({value, maxValue, style}) => {
  let colors = ['red', 'orange', 'yellow', 'olive', 'green']
  let clrIdx = Math.floor(value / maxValue * 4)
  if (value !== 0 && clrIdx === 0) {
    clrIdx = 1
  }

  return (
    <Progress value={value} total={maxValue} progress='percent' style={style} color={colors[clrIdx]} />
  )
}

ProgressBar.propTypes = {
  value: PropTypes.number.isRequired,
  maxValue: PropTypes.number.isRequired,
  style: PropTypes.string.isRequired
}

export default ProgressBar
