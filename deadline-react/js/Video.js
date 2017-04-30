import React from 'react'

const Video = () => {
  return (
    <video autoPlay loop className='video'>
      <source src='assets/Love-Coding.mp4' type='video/mp4' />
      Your browser does not support HTML5 video.
    </video>
  )
}

export default Video
