import React from 'react'
import Challenge from './Challenge'
import { getSubCategoryChallenges } from '../../requests'
import { convertFromUrlToFriendlyText } from '../../helpers'

class ChallengesPage extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      challenges: []
    }

    this.loadSubcategoryChallenges = this.loadSubcategoryChallenges.bind(this)
    this.loadSubcategoryChallenges()
  }

  loadSubcategoryChallenges () {
    const subcategory = convertFromUrlToFriendlyText(window.localStorage.subcategory)
    console.log('Querying with ' + subcategory)
    getSubCategoryChallenges(subcategory).then(subcat => {
      let challenges = subcat.challenges
      this.setState(() => ({challenges}))
    })
  }

  render () {
    const category = window.localStorage.subcategory

    return (
      <section className='challenges-page main'>
        <header>
          <h2 className='subcategory-name'>{category}</h2>
          <div className='subcategories'>
            subcategories
          </div>
        </header>
        <ul className='challenges'>
          {this.state.challenges.map(challenge => {
            return <Challenge
              key={challenge.id}
              name={challenge.name}
              difficulty={challenge.difficulty}
              score={challenge.score} />
          })}
        </ul>
      </section>
    )
  }
}

export default ChallengesPage
