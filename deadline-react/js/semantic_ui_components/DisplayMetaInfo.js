/* Card component for displaying meta information */
import React from 'react'
import PropTypes from 'prop-types'
import { Link } from 'react-router-dom'
import { Card, Button, Rating } from 'semantic-ui-react'
import { getChallengeDetailsLink } from '../helpers.js'

const DisplayMetaInfo = ({id, rating, score, name}) => (
  <Card>
    <Card.Content>
      <Card.Header>
        {name}
      </Card.Header>
      <Card.Meta>
        Rating: <Rating icon='star' defaultRating={rating} maxRating={7} />
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
  </Card>
)

DisplayMetaInfo.propTypes = {
  id: PropTypes.number.isRequired,
  rating: PropTypes.number,
  score: PropTypes.number,
  name: PropTypes.string
}

export default DisplayMetaInfo
