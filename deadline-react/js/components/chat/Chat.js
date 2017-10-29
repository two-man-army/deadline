import React from 'react'
import ChatWindow from './ChatWindow'
import ChatList from './ChatList'

class Chat extends React.Component {
  render () {
    return (
      <section className='main chat'>
        <ChatList />
        <ChatWindow />
      </section>
    )
  }
}

export default Chat
