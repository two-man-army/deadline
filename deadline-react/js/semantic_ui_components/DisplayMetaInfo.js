/* Card component for displaying meta information */
import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'
import {Card, Button} from 'semantic-ui-react'
import StarRatingComponent from 'react-star-rating-component'
import { getChallengeDetailsLink } from '../helpers.js'
import ProgressBar from './ProgressBar.js'

const DisplayMetaInfo = ({id, difficulty, score, name, userScore}) => (
  <Card>
    <Card.Content>
      <Card.Header>
        {name}
      </Card.Header>
      <Card.Meta className='challenge-meta-info-difficulty'>
        Difficulty:
        <StarRatingComponent
          editing={false} value={difficulty} starCount={10}
          renderStarIcon={(index, value) => {
            return <span className={index <= value ? 'fa fa-star' : 'fa fa-star-o'} style={{color: 'rgb(255, 180, 0)'}} />
          }}
          renderStarIconHalf={() => <span className='fa fa-star-half' />} />
      </Card.Meta>
    </Card.Content>
    <Card.Content extra>
      Score: {score}
      <div className='go-to-challenge'>
        <Link to={getChallengeDetailsLink(id)}>
          <Button basic color='green'>To Challenge</Button>
        </Link>
      </div>
    </Card.Content>
    <Card.Content extra>
      <ProgressBar value={userScore} maxValue={score} />
    </Card.Content>
  </Card>
)
DisplayMetaInfo.propTypes = {
  id: PropTypes.number.isRequired,
  difficulty: PropTypes.number,
  score: PropTypes.number,
  userScore: PropTypes.number,
  name: PropTypes.string
}

export default DisplayMetaInfo
