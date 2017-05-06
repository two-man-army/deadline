import React from 'react'
import PropTypes from 'prop-types'
import { Icon, Header, Image, Table } from 'semantic-ui-react'
import TimeAgo from 'react-timeago'

class SubmissionsTable extends React.Component {
  constructor (props) {
    super(props)

    this.buildSubmissionRow = this.buildSubmissionRow.bind(this)
  }
  buildSubmissionRow (submission) {
    let submissionStatusIcon = null
    if (submission.pending) {
      submissionStatusIcon = <Icon size='small' color='orange' name='spinner' loading />
    } else {
      if (submission.compiled && submission.result_score !== 0) {
        if (submission.result_score === this.props.maxScore) {
          submissionStatusIcon = <Icon size='small' color='green' name='checkmark' />
        } else {
          submissionStatusIcon = <Icon size='small' color='orange' name='star half' />
        }
      } else {
        submissionStatusIcon = <Icon size='small' color='red' name='remove' />
      }
    }

    let langIconStyle = {
      width: '20px',
      height: '20px',
      display: 'inline',
      marginRight: '10px'
    }
    return (
      <Table.Row key={submission.id}>
        <Table.Cell>
          <Header as='p' icon style={{'fontSize': '10px'}}>
            {submissionStatusIcon}
          </Header>
        </Table.Cell>
        <Table.Cell>
          {`${submission.result_score}/${this.props.maxScore}`}
        </Table.Cell>
        <Table.Cell>
          <Image src={`/assets/img/avatars/small/${submission.language.toLowerCase()}.png`} style={langIconStyle} />
          {submission.language}
        </Table.Cell>
        <Table.Cell>
          <TimeAgo date={submission.created_at} />
        </Table.Cell>
      </Table.Row>
    )
  }

  render () {
    return (
      <Table basic='very' celled collapsing style={{margin: '20px auto'}} >
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Status</Table.HeaderCell>
            <Table.HeaderCell>Score</Table.HeaderCell>
            <Table.HeaderCell>Language</Table.HeaderCell>
            <Table.HeaderCell>Submitted</Table.HeaderCell>
          </Table.Row>
        </Table.Header>

        <Table.Body>
          {this.props.submissions.map(submission => {
            return this.buildSubmissionRow(submission)
          })}
        </Table.Body>
      </Table>
    )
  }
}

SubmissionsTable.propTypes = {
  maxScore: PropTypes.number,
  submissions: PropTypes.array
}

export default SubmissionsTable
