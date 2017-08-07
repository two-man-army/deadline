import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'

const Category = ({name, url}) => (
  <li className='category'>
    <Link to={{pathname: url}}>
      <section>
        <h3 className='category-header'>{name}</h3>
        <div className='category-info'>
          <div className='progress-subcategories'>.</div>
          <div className='progress-challenges'>.</div>
        </div>
      </section>
    </Link>
  </li>
)

Category.propTypes = {
  name: PropTypes.string,
  url: PropTypes.string
}

export default Category
