import React from 'react'
import { Link } from 'react-router-dom'
import Search from './Search'

const Header = () => (
  <header className='page-header'>
    <nav>
      <div className='logo-container'>
        <Link to=''>
          <img className='logo' src={'assets/img/header/logo.png'} alt='' />
        </Link>
      </div>
      <div className='nav-search'>
        <Search />
      </div>
      <div className='nav-icons'>
        <img src='assets/img/header/email.svg' alt='' />
        <img src='assets/img/header/bell.svg' alt='' />
        <img src='assets/img/header/settings.svg' alt='' />
        <img src='assets/img/header/logout.svg' alt='' />
      </div>
    </nav>
  </header>
)

export default Header
