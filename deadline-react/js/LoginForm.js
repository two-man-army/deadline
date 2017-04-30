import React from 'react'
import PropTypes from 'prop-types'

const LoginForm = ({onSubmit, onChange}) => (
  <form onSubmit={onSubmit}>
    <div className='sign-in-htm'>
      <div className='group'>
        <label htmlFor='login-email' className='label'>Email</label>
        <input
          id='login-email'
          type='text'
          name='email'
          className='input'
          onChange={onChange}
        />
      </div>
      <div className='group'>
        <label htmlFor='pass' className='label'>Password</label>
        <input
          id='pass'
          type='password'
          name='password'
          className='input'
          data-type='password'
          onChange={onChange}
        />
      </div>
      <div className='group'>
        <input
          id='check'
          type='checkbox'
          className='check'
          defaultChecked
        />
        <label htmlFor='check'><span className='icon' /> Keep me Signed in</label>
      </div>
      <div className='group'>
        <input type='submit' className='button' value='Sign In' />
      </div>
      <div className='hr' />
      <div className='foot-lnk'>
        <a href='#forgot'>Forgot Password?</a>
      </div>
    </div>
  </form>
)

LoginForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired
}

export default LoginForm
