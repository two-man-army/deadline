import React from 'react'
import SweetAlert from 'sweetalert-react'
import LoginForm from './LoginForm'
import RegisterForm from './RegisterForm'
import Video from './Video'
import Auth from './auth.js'
import { postLogIn, postRegister } from './requests'
import { SweetAlertError } from './errors'
import { Redirect } from 'react-router-dom'

class LoginPage extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      user: {
        username: '',
        email: '',
        password: '',
        repeatedPassword: ''
      },
      repeatedPasswordIsInvalid: false,
      showAlert: false,
      alertTitle: '',
      alertDesc: '',
      redirectTo: ''
    }

    this.processLoginForm = this.processLoginForm.bind(this)
    this.processRegisterForm = this.processRegisterForm.bind(this)
    this.handleLoginData = this.handleLoginData.bind(this)
    this.handleRegisterData = this.handleRegisterData.bind(this)
  }

  handleLoginData (e) {
    const field = e.target.name
    const user = this.state.user
    user[field] = e.target.value

    this.setState({
      user
    })
  }

  handleRegisterData (e) {
    const field = e.target.name
    const user = this.state.user
    user[field] = e.target.value
    // TODO compare passwords & validate data

    if (user.password !== user.repeatedPassword) {
      this.setState({
        user,
        repeatedPasswordIsInvalid: true
      })
    } else {
      this.setState({
        user,
        repeatedPasswordIsInvalid: false
      })
    }
  }

  processLoginForm (e) {
    e.preventDefault()
    let user = this.state.user

    postLogIn(user.email, user.password).then(resp => {
      this.setState({
        redirectTo: '/'
      })
    }).catch(err => {
      throw err
    })
  }

  processRegisterForm (e) {
    e.preventDefault()

    let {email, password, username, repeatedPassword} = this.state.user

    if (password !== repeatedPassword) {
      this.setState({
        // user: this.state.user,
        // repeatedPasswordIsInvalid: true,
        showAlert: true,
        alertDesc: 'Your passwords dont match!',
        alertTitle: 'Invalid passwords!'
      })
    } else {
      postRegister(email, password, username).then(resp => {
        this.setState({
          redirectTo: '/'
        })

        console.log(resp)
      }).catch(err => {
        console.log(typeof err)
        if (err instanceof SweetAlertError) {
          this.setState({
            showAlert: true,
            alertDesc: err.message,
            alertTitle: err.title
          })
        } else {
          console.log(err)
        }
      })
        // TODO: Redirect ?
    }
  }

  render () {
    if (Auth.isUserAuthenticated()) {
      return <Redirect to={this.state.redirectTo} />
    }

    return (
      <div>
        <div className='login-wrap'>
          <div className='login-html'>
            <input
              id='tab-1'
              type='radio'
              name='tab'
              className='sign-in'
              defaultChecked
            />
            <SweetAlert
              type='error'
              show={this.state.showAlert}
              title={this.state.alertTitle}
              text={this.state.alertDesc}
              onConfirm={() => this.setState({ showAlert: false })}
            />
            <label htmlFor='tab-1' className='tab'>Sign In</label>
            <input
              id='tab-2'
              type='radio'
              name='tab'
              className='sign-up'
            />
            <label htmlFor='tab-2' className='tab'>Sign Up</label>
            <div className='form-container'>
              <LoginForm
                onSubmit={this.processLoginForm}
                onChange={this.handleLoginData}
                />
              <RegisterForm
                onSubmit={this.processRegisterForm}
                onChange={this.handleRegisterData}
                repeatedPasswordIsInvalid={this.state.repeatedPasswordIsInvalid}
              />
            </div>
          </div>
        </div>
        <Video />
      </div>
    )
  }
}

export default LoginPage
