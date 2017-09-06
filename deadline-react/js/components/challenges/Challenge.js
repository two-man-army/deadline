import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'
import { Circle } from 'rc-progress'

const Challenge = ({
  name,
  url,
  score,
  difficulty
  }) => (
    <li className='challenge'>
      <Link to={{pathname: url}}>
        <section className='challenge-info'>
          <div>
            <h3 className='challenge-name'>{name}</h3>
            <p className='difficulty'>Difficulty: {difficulty}/10</p>
            <p className='score'>Score: {score}</p>
          </div>
          <div className='success-rate'>
            <Circle
              percent='30'
              strokeWidth='4'
              trailWidth='3'
              strokeColor='red' />
          </div>
        </section>
      </Link>
    </li>
)

Challenge.propTypes = {
  name: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  score: PropTypes.number.isRequired,
  difficulty: PropTypes.number.isRequired
}

export default Challenge
