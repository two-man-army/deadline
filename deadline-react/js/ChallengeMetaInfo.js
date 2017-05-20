import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'

import {getChallengeDetailsLink} from './helpers.js'

const ChallengeMetaInfo = ({id, difficulty, score, name}) => (
  <Link to={getChallengeDetailsLink(id)}>
    <div className='challenge-meta-info'>
      <div className='challenge-meta-header'>
        <h1>{name}</h1>
      </div>
      <div className='challenge-meta-content'>
        <p>Rating: {difficulty}</p>
        <p>Score: {score}</p>
      </div>
    </div>
  </Link>
)

ChallengeMetaInfo.propTypes = {
  id: PropTypes.number.isRequired,
  difficulty: PropTypes.number,
  score: PropTypes.number,
  name: PropTypes.string
}

export default ChallengeMetaInfo
