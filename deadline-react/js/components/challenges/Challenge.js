import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'

const Challenge = ({
  name,
  url,
  score,
  difficulty,
  onClick}) => (
    <li data-subcategory-name={name} className='challenge' onClick={onClick}>
      <Link to={{pathname: url}}>
        <section>
          <div className='challenge'>
            <h3>{name}</h3>
            <p>Difficulty: {difficulty}</p>
            <p>Score: {score}</p>
          </div>
          <div className='success-rate'>70%</div>
        </section>
      </Link>
    </li>
)

Challenge.propTypes = {
  name: PropTypes.string.isRequired,
  url: PropTypes.string,
  score: PropTypes.number,
  difficulty: PropTypes.number,
  onClick: PropTypes.func
}

export default Challenge
