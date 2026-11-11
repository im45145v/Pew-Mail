import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import EmailEditor from './features/email-editor/EmailEditor';
import TestingLab from './features/testing-lab/TestingLab';
import './features/email-editor/EmailEditor.css';
import './App.css';

function App() {
  const handleSave = (emailDocument: any) => {
    console.log('Saving email:', emailDocument);
    // In a real implementation, this would call the backend API
  };

  return (
    <Router>
      <div className="App">
        <nav className="main-navigation">
          <ul>
            <li>
              <Link to="/">Email Editor</Link>
            </li>
            <li>
              <Link to="/testing-lab">Testing Lab</Link>
            </li>
          </ul>
        </nav>
        
        <Routes>
          <Route path="/" element={
            <EmailEditor 
              projectId="test-project-id" 
              onSave={handleSave} 
            />
          } />
          <Route path="/testing-lab" element={<TestingLab />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
                <img className="button-icon" src={reactLogo} alt="" />
                Learn more
              </a>
            </li>
          </ul>
        </div>
        <div id="social">
          <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#social-icon"></use>
          </svg>
          <h2>Connect with us</h2>
          <p>Join the Vite community</p>
          <ul>
            <li>
              <a href="https://github.com/vitejs/vite" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#github-icon"></use>
                </svg>
                GitHub
              </a>
            </li>
            <li>
              <a href="https://chat.vite.dev/" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#discord-icon"></use>
                </svg>
                Discord
              </a>
            </li>
            <li>
              <a href="https://x.com/vite_js" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#x-icon"></use>
                </svg>
                X.com
              </a>
            </li>
            <li>
              <a href="https://bsky.app/profile/vite.dev" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#bluesky-icon"></use>
                </svg>
                Bluesky
              </a>
            </li>
          </ul>
        </div>
      </section>

      <div className="ticks"></div>
      <section id="spacer"></section>
    </>
  )
}

export default App
