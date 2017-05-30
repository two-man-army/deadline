import React from 'react'
import PropTypes from 'prop-types'
import { Header, Table } from 'semantic-ui-react'
import { getOverallLeaderboard } from '../requests.js'

class OverallLeaderboard extends React.Component {
  /**
   * Represents the overall Leaderboard Table for all users
   */
  constructor (props) {
    super(props)

    this.state = {
      users: []
    }

    this.loadUsers = this.loadUsers.bind(this)
    this.loadUsers()
  }

  loadUsers () {
    getOverallLeaderboard().then(users => {
      this.setState({users})
    })
  }

  render () {
    return (
      <Table basic='very' style={{margin: '20px auto', padding: '0 20px'}} >
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Position</Table.HeaderCell>
            <Table.HeaderCell>User</Table.HeaderCell>
            <Table.HeaderCell>Score</Table.HeaderCell>
          </Table.Row>
        </Table.Header>

        <Table.Body>
          {this.state.users.map((user, idx) => {
            return (
              <Table.Row key={idx}>
                <Table.Cell>
                  {user.position}
                </Table.Cell>
                <Table.Cell>
                  <Header as='h3' >
                    {user.name}
                  </Header>
                </Table.Cell>
                <Table.Cell>
                  {user.score}
                </Table.Cell>
              </Table.Row>
            )
          })}
        </Table.Body>
      </Table>
    )
  }
}

OverallLeaderboard.propTypes = {
  users: PropTypes.array
}

export default OverallLeaderboard
