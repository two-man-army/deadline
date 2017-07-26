import React from 'react'
import Category from './Category'
import { getCategoriesMetaInfo } from '../requests.js'

class CategoryPage extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      categories: []
    }

    this.loadCategories = this.loadCategories.bind(this)
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

  render () {
    return (
      <section>
        <ul>
          {this.state.categories.map(category => {
            return <Category name={category.name} />
          })}
        </ul>
      </section>
    )
  }
}

export default CategoryPage
