import React from 'react'

const RanklistBoxData = () => (
  <section className='ranklist'>
    <div className='ranklist-box-header'>
      <h4>Ranklist</h4>
      <div>
        <span className='users-to-follow'>The Users You Follow</span>
        <span className='all-users'>All Users</span>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>USER</th>
          <th>Score</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>1</td>
          <td>John Snow</td>
          <td>10</td>
        </tr>
        <tr>
          <td>2</td>
          <td>John Doe</td>
          <td>40</td>
        </tr>
        <tr>
          <td>3</td>
          <td>Jane Snow</td>
          <td>20</td>
        </tr>
      </tbody>
    </table>
  </section>
)

export default RanklistBoxData
