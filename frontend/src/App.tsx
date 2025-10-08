import React from 'react';
import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ProfileViewPage from './pages/ProfileViewPage';
import CreateProfilePage from './pages/CreateProfilePage';
import UpdateProfilePage from './pages/UpdateProfilePage';
import DataReviewPage from './pages/DataReviewPage';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="app-header marine-blue">
        <div className="container">
          <h1>Marine FITREP Assistance Tool</h1>
          <p>FITREP Profile Builder and Analysis Tool</p>
        </div>
      </header>
      
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/profile/:officerId" element={<ProfileViewPage />} />
          <Route path="/create-profile" element={<CreateProfilePage />} />
          <Route path="/update-profile/:officerId" element={<UpdateProfilePage />} />
          <Route path="/data-review" element={<DataReviewPage />} />
        </Routes>
      </main>
      
      <footer className="app-footer">
        <div className="container">
          <p>&copy; 2025 FITREP Assistance Tool - For Official Use Only</p>
        </div>
      </footer>
    </div>
  );
}

export default App;