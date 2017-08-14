import React from 'react'
import Category from './Category'
import { getCategoriesMetaInfo } from '../../requests.js'
import { convertToUrlFriendlyText } from '../../helpers.js'

class CategoryPage extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      categories: []
    }

    this.loadCategories = this.loadCategories.bind(this)
    this.storeCategoryDetails = this.storeCategoryDetails.bind(this)
    this.loadCategories()
  }

  loadCategories () {
    getCategoriesMetaInfo().then(categories => {
      this.setState(() => {
        return {
          categories
        }
      })
    })
  }

  storeCategoryDetails (e) {
    const categoryName = e.currentTarget.dataset.categoryName
    const categoryId = e.currentTarget.id

    window.localStorage.categoryId = categoryId
    window.localStorage.categoryName = categoryName
  }

  render () {
    return (
      <section className='category-page main'>
        <h2>Categories</h2>
        <ul className='categories'>
          {this.state.categories.map(category => {
            const categoryInURL = convertToUrlFriendlyText(category.name)
            return <Category id={category.id} data-category-name={category.name} key={category.id} name={category.name} url={`/categories/${categoryInURL}`} onClick={this.storeCategoryDetails} />
          })}
          <Category name='Test category' />
          <Category name='Test category' />
          <Category name='Test category' />
          <Category name='Test category' />
          <Category name='Test category' />
        </ul>
      </section>
    )
  }
}

export default CategoryPage
