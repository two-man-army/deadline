import React from 'react'
import PropTypes from 'prop-types'
import { Container } from 'semantic-ui-react'
import { getSubCategoryChallenges } from './requests'
import { convertFromUrlToFriendlyText } from './helpers'
import DisplayMetaInfo from './semantic_ui_components/DisplayMetaInfo'

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
      <Container>
        <div>
          <h1 style={{margin: '20px 83px'}}>{convertFromUrlToFriendlyText(this.subCategory)} Challenges</h1>
          {this.state.challenges.length === 0 &&
            <p>There are no challenges for this category.</p>
          }
          {this.state.challenges.map(challenge => {
            return <DisplayMetaInfo key={challenge.id} {...challenge} userScore={challenge.user_max_score} />
          })}
        </div>
      </Container>
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
