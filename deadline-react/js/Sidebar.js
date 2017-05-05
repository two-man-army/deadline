import React from 'react'
import MetisMenu from 'react-metismenu'
import { getCategoriesMetaInfo } from './requests.js'
import { convertToUrlFriendlyText } from './helpers.js'

class SideBar extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      loadedCategories: false,
      categories: []
    }

    this.loadCategories = this.loadCategories.bind(this)
    this.buildSidebarContent = this.buildSidebarContent.bind(this)
    this.loadCategories()
  }

  /**
   * Load the categories from the server and display them
   */
  loadCategories () {
    getCategoriesMetaInfo().then(categories => {
      this.setState({
        loadedCategories: true,
        categories
      })
    })
  }

  /**
   * Create the array of categories to be passed down to the MetisMenu component
   */
  buildSidebarContent () {
    let content = [
      {
        icon: 'dashboard',
        label: 'Dashboard',
        to: '/#/'
      }
    ]
    content = content.concat(this.state.categories.map(category => {
      return {
        label: category.name,
        content: category.sub_categories.map(subCategory => {
          return {
            label: subCategory,
            to: `/#/categories/${convertToUrlFriendlyText(subCategory)}`
          }
        })
      }
    }))
    return content
  }

  render () {
    if (!this.state.loadedCategories) {
      return <div style={{background: '#2c3e50', color: '#FFF', width: 220, height: window.innerHeight}} />
    }
    return <MetisMenu content={this.buildSidebarContent()} />
  }
}

export default SideBar
