import React from 'react'
import { Input, Dropdown } from 'semantic-ui-react'
import { postCourse } from './requests'

class CreateCourse extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      course: {
        name: '',
        languages: [],
        difficulty: ''
      }
    }

    this.createCourse = this.createCourse.bind(this)
    this.handleChange = this.handleChange.bind(this)
    this.handleLangSelection = this.handleLangSelection.bind(this)
  }

  handleChange (e) {
    const field = e.target.name
    const course = this.state.course
    course[field] = e.target.value

    this.setState({
      course
    })
  }

  handleLangSelection (e, lang) {
    const course = this.state.course
    course.languages = lang.value

    this.setState({
      course
    })
  }

  createCourse (e) {
    e.preventDefault()
    const name = this.state.course.name
    const languages = this.state.course.languages
    const difficulty = this.state.course.difficulty

    postCourse(name, languages, difficulty)
  }

  render () {
    // should be replaced with dynamic data
    const languages = [
      {key: 'PY', value: '1', text: 'Python'},
      {key: 'CPP', value: '2', text: 'C++'}
    ]

    return (
      <form action=''>
        <div><Input name='name' value={this.state.course.name} onChange={this.handleChange} placeholder='Course name..' /></div>
        <div><Input name='difficulty' value={this.state.course.difficulty} onChange={this.handleChange} placeholder='Difficulty..' /></div>
        <div><Dropdown onChange={this.handleLangSelection} multiple search selection options={languages} placeholder='Languages..' /></div>
        <button type='submit' onClick={this.createCourse}>Create</button>
      </form>
    )
  }
}

export default CreateCourse
