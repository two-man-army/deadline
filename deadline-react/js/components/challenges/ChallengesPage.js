import React from 'react'
import Challenge from './Challenge'
import { Link } from 'react-router-dom'
import { getSubCategoryChallenges } from '../../requests'
import { convertFromUrlToFriendlyText } from '../../helpers'
import SelectionSearch from '../../semantic_ui_components/SelectionSearch.js'

class ChallengesPage extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      challenges: [],
    }
    this.subcategories = ['Recursion', 'Sorting', 'Greedy', 'Strings', 'Graphs', 'Miscellaneous']

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
        <header className='challenges-header'>
          <div className='current-subcategory'>
            <h2 className='subcategory-name'>{category}</h2>
            <p>some progress bar here</p>
          </div>
          <div className='challenges-nav'>
            <ul>
              {this.subcategories.map(subcat => <li><Link to=''>{subcat}</Link></li>)}
              <li>foo</li>
              <li>foo</li>
              <li>foo</li>
              <li>foo</li>
              <li>foo</li>
              <li>foo</li>
            </ul>
            <SelectionSearch />
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
