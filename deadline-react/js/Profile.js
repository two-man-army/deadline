import React from 'react'
// import PropTypes from 'prop-types'

class Profile extends React.Component {
  render () {
    return (
      <section className='profile-page'>
        <ul>
          <li>Change password</li>
          <li>Edit profile</li>
          <li>Something else</li>
        </ul>
        <article>Load different form for different options</article>
      </section>
    )
  }
}

export default Profile
