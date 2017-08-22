import React from 'react'
import Subcategory from './Subcategory'
import { getCategorySubcategories } from '../../requests'
import { convertToUrlFriendlyText } from '../../helpers.js'

class SubcategoriesPage extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      subcategories: []
    }

    this.loadSubcategories = this.loadSubcategories.bind(this)
    this.storeSubcategoryDetails = this.storeSubcategoryDetails.bind(this)
    this.calculateCompletedPercenage = this.calculateCompletedPercenage.bind(this)
    this.expToNextProficiency = this.expToNextProficiency.bind(this)
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

  storeSubcategoryDetails (e) {
    const subcategoryName = e.currentTarget.dataset.subcategoryName
    window.localStorage.subcategory = subcategoryName
  }

  /**
   * Calculates the needed exp. (score) to the next proficiency.
   *
   */
  expToNextProficiency (neededPercentage, maxScore, userScore) {
    const neededScore = (neededPercentage * maxScore) / 100

    return neededScore - userScore
  }

  calculateCompletedPercenage (challengeCount, solvedChallengesCount) {
    if (solvedChallengesCount === 0) {
      return 0
    }

    const percentageCompleted = (solvedChallengesCount / challengeCount) * 100

    return percentageCompleted.toFixed(2)
  }

  render () {
    const mainCategory = window.localStorage.categoryName
    const nextUrl = `/categories/${convertToUrlFriendlyText(mainCategory)}`
    // remove hard coded values below once we have real data.

    return (
      <section className='subcategories-page main'>
        <h1 className='main-category'>{mainCategory}</h1>
        <ul className='subcategories'>
          {this.state.subcategories.map(subcategory => {
            return <Subcategory
              key={subcategory.name}
              url={`${nextUrl}/${convertToUrlFriendlyText(subcategory.name)}`}
              onClick={this.storeSubcategoryDetails}
              name={subcategory.name}
              proficiency={subcategory.proficiency.name}
              challengeCount={subcategory.challenge_count}
              solvedChallenges={subcategory.solved_challenges_count}
              percentageCompleted={
                this.calculateCompletedPercenage(
                  subcategory.challenge_count,
                  subcategory.solved_challenges_count)
              }
              nextProficiency={subcategory.next_proficiency.name}
              expToNextProficiency={
                this.expToNextProficiency(
                  subcategory.next_proficiency.needed_percentage,
                  1000,
                  150)} />
          })}
        </ul>
      </section>
    )
  }
}

export default SubcategoriesPage
