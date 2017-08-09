import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'

const Subcategory = ({url, name}) => (
  <li className='subcategory'>
    <Link to={{pathname: url}}>
      <section>
        <header>
          <h3 className='subcat-header'>{name}</h3>
        </header>
        <div>
          <span className='subcat-difficulty'>
            Difficulty: 3.5/10
          </span>
        </div>
        <div>
          <span className='subcat-score'>Score: 30</span>
        </div>
      </section>
    </Link>
  </li>
)

Subcategory.propTypes = {
  url: PropTypes.string,
  name: PropTypes.string
}

export default Subcategory
