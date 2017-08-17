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
    this.calculateCompletedPercenage = this.calculateCompletedPercenage.bind(this)
    this.expToNextProficiency = this.expToNextProficiency.bind(this)
    this.expToNextProficiency(1000, 850)
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

  // TODO round two digits after the decimal point
  /**
   * Calculates the needed exp. to the next proficiency.
   *
   */
  expToNextProficiency (maxScore, userScore) {
    const percentageToMaxScore = (100 - ((userScore / maxScore) * 100))
    const requiredExp = (percentageToMaxScore / 100) * maxScore

    return requiredExp
  }

  calculateCompletedPercenage (challengeCount, solvedChallengesCount) {
    if (solvedChallengesCount === 0) {
      return 0
    }

    // TODO round two digits after the decimal point
    const percentageCompleted = (solvedChallengesCount / challengeCount) * 100

    return percentageCompleted
  }

  render () {
    const mainCategory = window.localStorage.categoryName
    // remove hard coded values below once we have real data.

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
              solvedChallenges={subcategory.solved_challenges_count}
              percentageCompleted={
                this.calculateCompletedPercenage(
                  subcategory.challenge_count,
                  subcategory.solved_challenges_count)
              }
              nextProficiency={subcategory.next_proficiency.name}
              expToNextProficiency={
                this.expToNextProficiency(
                  1000,
                  850)} />
          })}
        </ul>
      </section>
    )
  }
}

export default SubcategoriesPage
