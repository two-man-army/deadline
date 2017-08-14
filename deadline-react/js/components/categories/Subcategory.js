import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'
import CategoryHeader from './CategoryHeader'

const Subcategory = ({url, name}) => (
  <li className='subcategory'>
    <Link to={{pathname: url}}>
      <section>
        <CategoryHeader name={name} />
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
  url: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired
}

export default Subcategory
