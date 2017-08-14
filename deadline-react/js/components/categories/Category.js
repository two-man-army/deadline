import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'
import CategoryHeader from './CategoryHeader'

const Category = ({id, name, url, onClick}) => (
  <li id={id} data-category-name={name} className='category' onClick={onClick}>
    <Link to={{pathname: url}}>
      <section>
        <CategoryHeader name={name} />
        <div className='category-info'>
          <div className='completed-subcategories'>
            <div className='subcat-progress'>
              5/7
            </div>
            <div className='subcat-text'>Subcategories</div>
          </div>
          <div className='completed-challenges'>
            <div className='challenges-progress'>
              511/700
            </div>
            <div className='status-text'>Completed</div>
          </div>
        </div>
      </section>
    </Link>
  </li>
)

Category.propTypes = {
  id: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  url: PropTypes.string,
  onClick: PropTypes.func
}

export default Category
