import React from 'react'
import ChatHeader from './ChatHeader'
import Search from '../Search'
import ChatThreadListRow from './ChatThreadListRow'

const ChatList = () => (
  <section className='chat-list'>
    <ChatHeader heading='Messages' />
    <Search />
    <ul className='ThreadListContainer'>
      <ChatThreadListRow name='Ivaelo Eleev' path='assets/img/pikachu.svg' msg='Hello hows a going mate are you...' time='21:12' />
      <ChatThreadListRow name='Cesar Vergas' path='assets/img/pikachu.svg' msg='Yesterday I was having a party...' time='10:43' />
    </ul>
  </section>
)

export default ChatList
