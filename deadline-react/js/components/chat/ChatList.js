import React from 'react'
import ChatHeader from './ChatHeader'
import Search from '../Search'
import ChatThreadListRow from './ChatThreadListRow'

const ChatList = () => (
  <section className='chat-list'>
    <ChatHeader heading='Messages' />
    <Search />
    <ChatThreadListRow name='Ivaelo Eleev' path='assets/img/pikachu.svg' msg='Hello hows a going mate are you...' />
    <ChatThreadListRow name='Cesar Vergas' path='assets/img/pikachu.svg' msg='Yesterday I was having a party...' />
  </section>
)

export default ChatList
