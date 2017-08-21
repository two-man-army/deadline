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
    console.log(this.state.challenges)

    return (
      <section className='category-page main'>
        <h2>{category}</h2>
        <ul className='challenges'>
          {this.state.challenges.map(challenge => {
            return <Challenge key={challenge.id} name={challenge.name} />
          })}
        </ul>
      </section>
    )
  }
}

export default ChallengesPage
