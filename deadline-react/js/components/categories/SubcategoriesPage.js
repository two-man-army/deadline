import React from 'react'
import Subcategory from './Subcategory'

class SubcategoriesPage extends React.Component {
  render () {
    return (
      <section className='subcategories-page main'>
        <h1>subcat page</h1>
        <ul className='subcategories'>
          <Subcategory />
          <Subcategory />
          <Subcategory />
          <Subcategory />
          <Subcategory />
          <Subcategory />
          <Subcategory />
          <Subcategory />
          <Subcategory />
        </ul>
      </section>
    )
  }
}

export default SubcategoriesPage
