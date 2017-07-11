import React from 'react'
import SuggestionItem from './SuggestionItem'

const FollowSuggestions = () => (
  <section className='follow-box'>
    <div className='follow-box-header'>
      <h4>You may want to follow</h4>
      <button type='submit'>
        <img src='assets/img/header/search.svg' alt='' />
      </button>
    </div>
    <ul>
      <SuggestionItem name='Erik Johnson' path='assets/img/sidebar/profile.png' />
      <SuggestionItem name='Frank Stone' path='assets/img/sidebar/profile.png' />
      <SuggestionItem name='Elizbeth Moss' path='assets/img/sidebar/profile.png' />
      <SuggestionItem name='David Shue' path='assets/img/sidebar/profile.png' />
    </ul>
    <button className='view-more-btn'>View more...</button>
  </section>
)

export default FollowSuggestions
