import React from 'react'
import PropTypes from 'prop-types'
import { Dropdown, Input, Icon, Header, Image, Table } from 'semantic-ui-react'
import TimeAgo from 'react-timeago'
import { postCastSubmissionVote, deleteRemoveSubmissionVote } from '../requests.js'

class LeaderboardTable extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      submissions: this.props.submissions,
      chosenSearchField: 'user',
      searchQuery: ''
    }

    const searchOptions = [
      { key: 'user', text: 'Author', value: 'user' },
      { key: 'language', text: 'Language', value: 'language' }
    ]

    this.searchOptions = searchOptions
    this.buildSubmissionRow = this.buildSubmissionRow.bind(this)
    this.filterSubmissionsBySearchQuery = this.filterSubmissionsBySearchQuery.bind(this)
    this.handleSearchTermChange = this.handleSearchTermChange.bind(this)
    this.handleSearch = this.handleSearch.bind(this)
    this.handleSubmissionDownvote = this.handleSubmissionDownvote.bind(this)
    this.handleSubmissionUpvote = this.handleSubmissionUpvote.bind(this)
    this.buildSubmissionVoteIcons = this.buildSubmissionVoteIcons.bind(this)
  }

  /**
   * Builds the submission row for a specific submission
   * @param {object} submission
   * @param {bool} withLinks - if we want to include a link to the code
   */
  buildSubmissionRow (submission, withLinks) {
    let submissionStatusIcon = null
    let iconSizeStyle = {'fontSize': '22px'}  // for some reason the size prop does not work
    if (submission.pending) {
      submissionStatusIcon = <Icon size='small' color='orange' name='spinner' loading style={iconSizeStyle} />
    } else {
      if (submission.compiled && submission.result_score !== 0) {
        if (submission.result_score === this.props.maxScore) {
          submissionStatusIcon = <Icon size='small' color='green' name='checkmark' style={iconSizeStyle} />
        } else {
          if (submission.timed_out) {
            // Submission has mostly timed out
            submissionStatusIcon = <Icon size='small' color='#810000' name='clock' style={iconSizeStyle} />
          } else {
            // Submission is partly solved
            submissionStatusIcon = <Icon size='small' color='orange' name='star half' style={iconSizeStyle} />
          }
        }
      } else {
        // Submission has failed
        if (submission.timed_out) {
          submissionStatusIcon = <Icon size='small' color='#810000' name='clock' style={iconSizeStyle} />
        } else {
          submissionStatusIcon = <Icon size='small' color='red' name='remove' style={iconSizeStyle} />
        }
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
          <Header as='h3' >
            {submission.author}
          </Header>
        </Table.Cell>
        <Table.Cell>
          {submissionStatusIcon}
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
        {this.buildSubmissionLink(withLinks, submission)}
        {this.buildSubmissionVoteIcons(withLinks, submission)}
      </Table.Row>
    )
  }

/**
 * Return a table cell with a link to the given submission
 * @param {boolean} toRender - bool indicating if we want to render the link
 * @param {*} submission
 */
  buildSubmissionLink (toRender, submission) {
    if (!toRender) {
      return
    }
    // TODO: Create a submission detail view and add link
    return <Table.Cell>{'LINK'}</Table.Cell>
  }

  buildSubmissionVoteIcons (toRender, submission) {
    if (!toRender) {
      return
    }
    let upvoteStyle = submission.user_has_voted && submission.user_has_upvoted ? {color: '#ff4081'} : undefined
    let downvoteStyle = submission.user_has_voted && !submission.user_has_upvoted ? {color: '#ff4081'} : undefined

    return (
      <Table.Cell>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          width: '10%'
        }}>
          <Icon size='large' link name='angle up' onClick={() => { this.handleSubmissionUpvote(submission.id, submission) }} style={upvoteStyle} />
          <Icon size='large' link name='angle down' onClick={() => { this.handleSubmissionDownvote(submission.id, submission) }} style={downvoteStyle} />
        </div>
        <p>{submission.upvote_count - submission.downvote_count}</p>
      </Table.Cell>
    )
  }
  handleSearch (ev, e) {
    let searchVal = e.value
    if (searchVal === '') {
      this.setState({submissions: this.props.submissions})
      return
    }

    let submissions = this.filterSubmissionsBySearchQuery(searchVal, this.state.chosenSearchField)
    this.setState({submissions, searchQuery: e.value})
  }

  handleSubmissionUpvote (submissionId, submission) {
    // TODO: Upvote

    if (submission.user_has_voted) {
      if (submission.user_has_upvoted) {
        // this removes the vote
        submission.upvote_count -= 1
        submission.user_has_voted = false
        submission.user_has_upvoted = false
        deleteRemoveSubmissionVote(submission.id)
      } else {
        // user has downvoted and now switches it to an upvote
        submission.downvote_count -= 1
        submission.upvote_count += 1
        submission.user_has_upvoted = true
        postCastSubmissionVote(submission.id, true)
      }
    } else {
      submission.upvote_count += 1
      submission.user_has_voted = true
      submission.user_has_upvoted = true
      postCastSubmissionVote(submission.id, true)
    }

    console.log(`User has voted: ${submission.user_has_voted}`)
    console.log(`Submission is upvoted: ${submission.user_has_upvoted}`)

    this.setState({submissions: this.state.submissions})
  }

  handleSubmissionDownvote (submissionId, submission) {
    if (submission.user_has_voted) {
      if (!submission.user_has_upvoted) {
        // this removes the vote
        submission.downvote_count -= 1
        submission.user_has_voted = false
        deleteRemoveSubmissionVote(submission.id)
      } else {
        // user removes his upvote and casts a downvote
        submission.upvote_count -= 1
        submission.downvote_count += 1
        submission.user_has_upvoted = false
        postCastSubmissionVote(submission.id, false)
      }
    } else {
      submission.downvote_count += 1
      submission.user_has_voted = true
      submission.user_has_upvoted = false
      postCastSubmissionVote(submission.id, false)
    }

    this.setState({submissions: this.state.submissions})
  }

  /**
   * Returns the submissions whose {searchField} starts with the given {searchVal}
   * i.e searchField = 'user', searchVal = 'mar' - will return only submissions from users whose author starts with Mar
   * @param {String} searchVal
   * @param {String} searchField
   */
  filterSubmissionsBySearchQuery (searchVal, searchField) {
    searchVal = searchVal.toLowerCase()
    searchField = searchField.toLowerCase()

    if (searchField === 'user') {  // filter by author
      return this.props.submissions.filter(submission => {
        return submission.author.toLowerCase().startsWith(searchVal)
      })
    } else if (searchField === 'language') {  // filter by language
      return this.props.submissions.filter(submission => {
        return submission.language.toLowerCase().startsWith(searchVal)
      })
    } else {
      return this.props.submissions
    }
  }

  /**
   * Handles the search term we're searching by change
   * i.e Author -> Language (we want to search by language now)
   * So re-query the search text for the different term
   */
  handleSearchTermChange (ev, e) {
    let submissions = this.filterSubmissionsBySearchQuery(this.state.searchQuery, e.value)
    this.setState({submissions, chosenSearchField: e.value})
  }

  /**
   * Reload the submissions props when we've received new info
   */
  componentWillReceiveProps (nextProps) {
    if (nextProps.submissions.length !== this.props.submissions.length) {
      this.setState({submissions: nextProps.submissions})  // this is subject to problems, i.e resetting search queries
    }
  }

  render () {
    let toRenderLinks = this.props.hasUnlockedSubmissions
    let linkHeader = toRenderLinks ? <Table.HeaderCell>Code</Table.HeaderCell> : null
    let voteHeader = toRenderLinks ? <Table.HeaderCell>Votes</Table.HeaderCell> : null

    return (
      <div>
        <Input
          action={<Dropdown basic floating options={this.searchOptions} defaultValue='user' onChange={this.handleSearchTermChange} />}
          icon='search'
          iconPosition='left'
          placeholder='Search...'
          onChange={this.handleSearch}
          className='leaderboard-search'
      />
        <Table basic='very' style={{margin: '20px auto', padding: '0 20px'}} >
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell>Author</Table.HeaderCell>
              <Table.HeaderCell>Status</Table.HeaderCell>
              <Table.HeaderCell>Score</Table.HeaderCell>
              <Table.HeaderCell>Language</Table.HeaderCell>
              <Table.HeaderCell>Submitted</Table.HeaderCell>
              {linkHeader}
              {voteHeader}
            </Table.Row>
          </Table.Header>

          <Table.Body>
            {this.state.submissions.map(submission => {
              return this.buildSubmissionRow(submission, toRenderLinks)
            })}
          </Table.Body>
        </Table>
      </div>
    )
  }
}

LeaderboardTable.propTypes = {
  maxScore: PropTypes.number,
  submissions: PropTypes.array,
  hasUnlockedSubmissions: PropTypes.bool
}

export default LeaderboardTable
