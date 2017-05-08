import React from 'react'
import Auth from '../auth'
import { Header } from 'grommet'
import { Button } from 'semantic-ui-react'
import ProfileOptions from './ProfileOptions'

const DashboardHeader = () => {
  const handleLogout = () => {
    Auth.deauthenticateUser()
    window.location.reload()
  }

  return (
    <Header className='dashboard-header'>
      <Button animated='fade' onClick={handleLogout} style={{color: '#ff5533', background: 'transparent', height: '100%'}}>
        <Button.Content visible>
          Logout
        </Button.Content>
        <Button.Content hidden>
          Bye! :)
        </Button.Content>
      </Button>
      <div className='user pull-right'>
        <div className='user-score'>
          <p>Score: placeholder</p>
        </div>
        <div className='notification-icon'>
          <i className='fa fa-bell-o' />
        </div>
        <ProfileOptions />
      </div>
    </Header>
  )
}

export default DashboardHeader
