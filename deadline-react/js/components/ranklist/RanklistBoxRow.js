import React from 'react'
import PropTypes from 'prop-types'

const RanklistBoxRow = ({name, position, score}) => (
  <tr>
    <td>{position}</td>
    <td>{name}</td>
    <td>{score}</td>
  </tr>
)

RanklistBoxRow.propTypes = {
  name: PropTypes.string.isRequired,
  position: PropTypes.number.isRequired,
  score: PropTypes.number.isRequired
}

export default RanklistBoxRow
