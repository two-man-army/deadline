import React from 'react'
import PropTypes from 'prop-types'

const CategoryHeader = ({name}) => (
  <header>
    <h3 className='category-header'>{name}</h3>
  </header>
)

CategoryHeader.propTypes = {
  name: PropTypes.string.isRequired
}

export default CategoryHeader
