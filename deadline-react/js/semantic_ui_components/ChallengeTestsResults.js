/* Provides a  Relaxed Horizontal List with Avatars */
import React from 'react'
import PropTypes from 'prop-types'
import { Icon, List } from 'semantic-ui-react'
import CircularProgress from 'material-ui/CircularProgress'

const ChallengeTestsResults = ({tests, toLoad}) => (
  <List horizontal relaxed>
    {tests.map((test, idx) => {
      let testIcon = null
      if (toLoad) {
        testIcon = <CircularProgress size={14} thickness={1} style={{display: 'inline'}} />
      } else {
        testIcon = test.success ? (
          <Icon color='green' name='checkmark' />
        ) : (
          <Icon color='red' name='remove' />
        )
        if (test.timed_out) {
          // set a timed out icon
          testIcon = <Icon color='#810000' name='clock' />
        }
      }

      return (
        <List.Item key={test.number}>
          {testIcon}
          <List.Content>
            <List.Header as='a'>{`Test Case #${test.number}`}</List.Header>
          </List.Content>
        </List.Item>
      )
    })}
  </List>
)

ChallengeTestsResults.propTypes = {
  tests: PropTypes.shape({
    number: PropTypes.number,
    success: PropTypes.boolean
  }),
  toLoad: PropTypes.boolean
}

export default ChallengeTestsResults
