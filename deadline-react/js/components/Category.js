import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'

const Category = ({name, url}) => (
  <li>
    <Link to={{pathname: url}}>
      <section>
        <h3>{name}</h3>
      </section>
    </Link>
  </li>
)

Category.propTypes = {
  name: PropTypes.string,
  url: PropTypes.string
}

export default Category
