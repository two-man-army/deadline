import React from 'react'
import PropTypes from 'prop-types'
import { Progress } from 'antd'

const TestCase = ({status, width}) => (
  <Progress type='circle' strokeWidth={3} percent={100} status={status} width={width} />
)

TestCase.propTypes = {
  status: PropTypes.string,
  width: PropTypes.number
}

export default TestCase
