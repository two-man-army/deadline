import React from 'react'
import NavItem from './NavItem'
import NavProfile from './NavProfile'

class SidebarNav extends React.Component {
  render () {
    return (
      <aside className='side-nav'>
        <nav>
          <NavProfile name='John Smith' path='assets/img/sidebar/profile.png' />
          <ul>
            <NavItem name='Home' path='assets/img/sidebar/home.png' url='/' />
            <NavItem name='Dashboard' path='assets/img/sidebar/dashboard.png' />
            <NavItem name='Challenges' path='assets/img/sidebar/challenges.png' url='challenges/categories' />
            <NavItem name='Ranklist' path='assets/img/sidebar/ranklist.png' />
          </ul>
        </nav>
      </aside>
    )
  }
}

export default SidebarNav
