import React from 'react'
import { Progress } from 'semantic-ui-react'

// TODO: Add different colors in regards to percentage
const ProgressBar = ({value, maxValue}) => (
  <Progress value={value} total={maxValue} progress='percent' />
)

ProgressBar.propTypes = {
  value: React.PropTypes.number.isRequired,
  maxValue: React.PropTypes.number.isRequired
}

export default ProgressBar
