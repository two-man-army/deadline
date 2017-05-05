import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'

import {getChallengeDetailsLink} from './helpers.js'

const ChallengeMetaInfo = ({id, rating, score, name}) => (
  <Link to={getChallengeDetailsLink(id)}>
    <div className='challenge-meta-info'>
      <div className='challenge-meta-header'>
        <h1>{name}</h1>
      </div>
      <div className='challenge-meta-content'>
        <p>Rating: {rating}</p>
        <p>Score: {score}</p>
      </div>
    </div>
  </Link>
)

ChallengeMetaInfo.propTypes = {
  id: PropTypes.number.isRequired,
  rating: PropTypes.number,
  score: PropTypes.number,
  name: PropTypes.string
}

export default ChallengeMetaInfo
