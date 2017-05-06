/* Provides a  Relaxed Horizontal List with Avatars */
import React from 'react'
import { Icon, List } from 'semantic-ui-react'

const ChallengeTestsResults = ({tests}) => (
  <List horizontal relaxed>
    {tests.map((test, idx) => {
      let testIcon = test.success ? (
        <Icon color='green' name='checkmark' />
      ) : (
        <Icon color='red' name='remove' />
      )

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

export default ChallengeTestsResults
