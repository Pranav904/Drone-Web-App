import React from 'react';
import MissionForm from './components/MissionForm';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Drone Mission Control</h1>
        <MissionForm />
      </header>
    </div>
  );
}

export default App;
