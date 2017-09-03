import React from 'react'
import PropTypes from 'prop-types'
import Challenge from './Challenge'
import { Link } from 'react-router-dom'
import { getSubCategoryChallenges, getCategorySubcategories } from '../../requests'
import { convertFromUrlToFriendlyText } from '../../helpers'
import SelectionSearch from '../../semantic_ui_components/SelectionSearch.js'

class ChallengesPage extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      subcategories: [],
      challenges: []
    }

    this.loadSubcategoryChallenges = this.loadSubcategoryChallenges.bind(this)
    this.loadSubcategories = this.loadSubcategories.bind(this)
    this.loadSubcategoryChallenges()
    this.loadSubcategories()
  }

  loadSubcategoryChallenges () {
    const subcategory = convertFromUrlToFriendlyText(this.props.match.params.subcategory)
    console.log('Querying with ' + subcategory)
    getSubCategoryChallenges(subcategory).then(subcat => {
      let challenges = subcat.challenges
      this.setState(() => ({challenges}))
    })
  }

  loadSubcategories () {
    const categoryName = convertFromUrlToFriendlyText(this.props.match.params.category)

    getCategorySubcategories(categoryName)
      .then(subcategories => {
        this.setState(() => {
          return {
            subcategories
          }
        })
      })
  }

  render () {
    const subcategory = convertFromUrlToFriendlyText(this.props.match.params.subcategory)

    return (
      <section className='challenges-page main'>
        <header className='challenges-header'>
          <div className='current-subcategory'>
            <h2 className='subcategory-name'>{subcategory}</h2>
            <p>some progress bar here</p>
          </div>
          <div className='challenges-nav'>
            <ul>
              {this.state.subcategories.filter(subcat => subcat.name !== subcategory)
                .map(subcat => <li><Link to=''>{subcat.name}</Link></li>)}
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
              url={`/challenges/${challenge.id}`}
              name={challenge.name}
              difficulty={challenge.difficulty}
              score={challenge.score} />
          })}
        </ul>
      </section>
    )
  }
}

ChallengesPage.propTypes = {
  match: PropTypes.string
}

export default ChallengesPage
