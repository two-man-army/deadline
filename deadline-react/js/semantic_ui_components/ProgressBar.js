import React from 'react'
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
  value: React.PropTypes.number.isRequired,
  maxValue: React.PropTypes.number.isRequired
}

export default ProgressBar
