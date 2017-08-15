import React from 'react'
import Subcategory from './Subcategory'
import { getCategorySubcategories } from '../../requests'

class SubcategoriesPage extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      subcategories: []
    }

    this.loadSubcategories = this.loadSubcategories.bind(this)
    this.loadSubcategories()
  }

  loadSubcategories () {
    const categoryId = window.localStorage.categoryId

    getCategorySubcategories(categoryId)
      .then(subcategories => {
        this.setState(() => {
          return {
            subcategories
          }
        })
      })
  }

  render () {
    const mainCategory = window.localStorage.categoryName

    return (
      <section className='subcategories-page main'>
        <h1 className='main-category'>{mainCategory}</h1>
        <ul className='subcategories'>
          {this.state.subcategories.map(subcategory => {
            return <Subcategory
              key={subcategory.name}
              name={subcategory.name}
              proficiency={subcategory.proficiency.name}
              challengeCount={subcategory.challenge_count}
              solvedChallenges={subcategory.solved_challenges_count} />
          })}
        </ul>
      </section>
    )
  }
}

export default SubcategoriesPage
