import React from 'react'
import PropTypes from 'prop-types'

const RegisterForm = ({onSubmit, onChange}) => (
  <form onSubmit={onSubmit}>
    <div className='sign-up-htm'>
      <div className='group'>
        <label htmlFor='username' className='label'>Username</label>
        <input
          id='username'
          type='text'
          name='username'
          className='input'
          onChange={onChange}
        />
      </div>
      <div className='group'>
        <label htmlFor='reg-pass' className='label'>Password</label>
        <input
          id='reg-pass'
          type='password'
          name='password'
          className='input'
          data-type='password'
          onChange={onChange}
        />
      </div>
      <div className='group'>
        <label htmlFor='repeat-pass' className='label'>Repeat Password</label>
        <input
          id='repeat-pass'
          type='password'
          name='repeatedPassword'
          className='input'
          data-type='password'
          onChange={onChange}
        />
      </div>
      <div className='group'>
        <label htmlFor='reg-email' className='label'>Email Address</label>
        <input
          id='reg-email'
          type='text'
          name='email'
          className='input'
          onChange={onChange}
        />
      </div>
      <div className='group'>
        <input
          type='submit'
          className='button'
          value='Sign Up'
        />
      </div>
      <div className='hr' />
      <div className='foot-lnk'>
        <label htmlFor='tab-1'>Already Member?</label>
      </div>
    </div>
  </form>
)

RegisterForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired
}

export default RegisterForm
