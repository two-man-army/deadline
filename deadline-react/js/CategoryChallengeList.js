import React from 'react'
import PropTypes from 'prop-types'
import {getSubCategoryChallenges} from './requests.js'
import ChallengeMetaInfo from './ChallengeMetaInfo.js'

class CategoryChallengeList extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      challenges: []
    }

    this.subCategory = props.match.params.category

    this.loadSubCategoryChallenges = this.loadSubCategoryChallenges.bind(this)
    this.loadSubCategoryChallenges()
  }

  loadSubCategoryChallenges () {
    console.log('Querying with ' + this.subCategory)
    getSubCategoryChallenges(this.subCategory).then(subCat => {
      let challenges = subCat.challenges
      this.setState({challenges})
    }).catch(err => {
      // TODO: Handle error
      throw err
    })
  }

  componentWillReceiveProps (nextProps) {
    if (nextProps.match.params.category !== this.subCategory) {
      // subCategory and URL has changed, therefore re-load and re-render challenges
      this.subCategory = nextProps.match.params.category
      this.loadSubCategoryChallenges()
    }
  }

  render () {
    return (
      <div>
        <h1>{this.subCategory} Challenges</h1>
        {this.state.challenges.map(challenge => {
          return <ChallengeMetaInfo {...challenge} />
        })}
      </div>
    )
  }
}

CategoryChallengeList.propTypes = {
  match: PropTypes.shape({
    params: PropTypes.shape({
      category: PropTypes.string.isRequired
    })
  })
}
export default CategoryChallengeList
