import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'

const Challenge = ({
  name,
  url,
  score,
  difficulty,
  onClick}) => (
    <li className='challenge' onClick={onClick}>
      <Link to={{pathname: url}}>
        <section className='challenge-info'>
          <div>
            <h3 className='challenge-name'>{name}</h3>
            <p className='difficulty'>Difficulty: {difficulty}/10</p>
            <p className='score'>Score: {score}</p>
          </div>
          <div className='success-rate'>70%</div>
        </section>
      </Link>
    </li>
)

Challenge.propTypes = {
  name: PropTypes.string.isRequired,
  url: PropTypes.string,
  score: PropTypes.number.isRequired,
  difficulty: PropTypes.number.isRequired,
  onClick: PropTypes.func
}

export default Challenge
