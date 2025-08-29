import React from 'react';
import './LandingPage.css';

const LandingPage = ({ onEnterTimeline }) => {
  return (
    <div className="landing-page">
      <div className="landing-content">
        <header className="landing-header">
          <h1>The Kleptocracy Timeline</h1>
          <p className="tagline">Open Source Intelligence for Democratic Defense</p>
          
          <button className="hero-enter-btn" onClick={onEnterTimeline}>
            View Interactive Timeline →
          </button>
        </header>

        <section className="cascade-framework">
          <h2>The Capture Cascade Framework</h2>
          <div className="cascade-explanation">
            <p className="cascade-intro">
              Democracy doesn't fall gradually—it cascades. Each captured institution enables 
              the capture of three more, creating exponential acceleration.
            </p>
            
            <div className="cascade-pattern">
              <div className="cascade-step">
                <span className="step-number">1</span>
                <strong>Capture Oversight</strong> → No one watching
              </div>
              <div className="cascade-step">
                <span className="step-number">2</span>
                <strong>Capture Courts</strong> → No legal recourse
              </div>
              <div className="cascade-step">
                <span className="step-number">3</span>
                <strong>Capture Enforcement</strong> → Selective prosecution
              </div>
              <div className="cascade-step">
                <span className="step-number">4</span>
                <strong>Capture Media</strong> → Public can't see
              </div>
              <div className="cascade-step">
                <span className="step-number">5</span>
                <strong>Cascade Accelerates</strong> → Each enables 3 more
              </div>
            </div>
            
            <div className="cascade-evidence">
              <p><strong>The Math is Terrifying:</strong></p>
              <div className="acceleration-stats">
                <span className="era">1970s: <strong><1</strong> event/year</span>
                <span className="era">2010s: <strong>8</strong> events/year</span>
                <span className="era">2020s: <strong>100+</strong> events/year</span>
              </div>
              <p className="cascade-warning">
                Once you see the cascade pattern, you can't unsee it. 
                Use this framework to understand what you're witnessing in real-time.
              </p>
            </div>
          </div>
        </section>

        <section className="mission">
          <h2>Our Mission</h2>
          <p>
            This timeline documents the systematic capture of American democracy through 
            verifiable events, court records, and public reporting. We're building a 
            living intelligence infrastructure that helps citizens understand and respond 
            to the erosion of democratic institutions.
          </p>
          <p>
            Every event is sourced, every pattern is documented, and every claim can be 
            verified. This is not conspiracy theory—it's conspiracy documentation.
          </p>
        </section>

        <section className="stats-preview">
          <div className="stat-card">
            <div className="stat-number">790</div>
            <div className="stat-label">Documented Events</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">3,000+</div>
            <div className="stat-label">Verified Sources</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">54</div>
            <div className="stat-label">Years Covered</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">9</div>
            <div className="stat-label">Capture Lanes</div>
          </div>
        </section>

        <section className="key-findings">
          <h2>Key Findings</h2>
          <ul>
            <li><strong>Cascade Acceleration:</strong> Each captured institution enables 3+ more captures, driving exponential growth from <1/year (1970s) to 100+/year (2020s)</li>
            <li><strong>Nine Capture Lanes:</strong> Judicial, Financial, Constitutional, Foreign Influence, Information Control, and more operating in parallel</li>
            <li><strong>Network Effects:</strong> Same 47 actors appear across 100+ events, showing coordinated capture not random corruption</li>
            <li><strong>Predictive Pattern:</strong> The cascade framework successfully predicts which institutions will be targeted next</li>
          </ul>
        </section>

        <section className="how-to-use">
          <h2>How to Use This Timeline</h2>
          <div className="usage-cards">
            <div className="usage-card">
              <h3>🔍 Explore</h3>
              <p>Browse chronologically or filter by capture lanes to see patterns emerge</p>
            </div>
            <div className="usage-card">
              <h3>📊 Analyze</h3>
              <p>Use the network view to see connections between actors and events</p>
            </div>
            <div className="usage-card">
              <h3>✅ Verify</h3>
              <p>Click any event to see sources and documentation</p>
            </div>
            <div className="usage-card">
              <h3>🤝 Contribute</h3>
              <p>Help validate events or submit new ones with sources</p>
            </div>
          </div>
        </section>

        <section className="cta-section">
          <button className="enter-timeline-btn" onClick={onEnterTimeline}>
            Enter the Timeline →
          </button>
          
          <div className="external-links">
            <a href="https://github.com/markramm/KleptocracyTimeline" 
               target="_blank" 
               rel="noopener noreferrer"
               className="link-card">
              <span className="link-icon">📁</span>
              <div>
                <div className="link-title">GitHub Repository</div>
                <div className="link-desc">View source code, data, and contribute</div>
              </div>
            </a>
            
            <a href="https://theramm.substack.com/s/essays-and-analysis" 
               target="_blank" 
               rel="noopener noreferrer"
               className="link-card">
              <span className="link-icon">📝</span>
              <div>
                <div className="link-title">Substack Newsletter</div>
                <div className="link-desc">Analysis and updates on emerging patterns</div>
              </div>
            </a>
          </div>
        </section>

        <section className="contribute">
          <h2>How to Contribute</h2>
          <div className="contribute-options">
            <div className="contribute-card">
              <h3>Validate Events</h3>
              <p>Help verify sources and fact-check timeline events</p>
              <a href="https://github.com/markramm/KleptocracyTimeline#validation" 
                 target="_blank" 
                 rel="noopener noreferrer">
                Learn More →
              </a>
            </div>
            <div className="contribute-card">
              <h3>Submit New Events</h3>
              <p>Add documented events with reliable sources</p>
              <a href="https://github.com/markramm/KleptocracyTimeline#contributing" 
                 target="_blank" 
                 rel="noopener noreferrer">
                Contribution Guide →
              </a>
            </div>
            <div className="contribute-card">
              <h3>Share & Discuss</h3>
              <p>Help spread awareness and join the conversation</p>
              <a href="https://github.com/markramm/KleptocracyTimeline/discussions" 
                 target="_blank" 
                 rel="noopener noreferrer">
                Join Discussion →
              </a>
            </div>
          </div>
        </section>

        <section className="disclaimer">
          <h2>About This Project</h2>
          <p>
            This is an open-source, community-driven effort to document the systematic 
            undermining of democratic institutions. All data is publicly available, all 
            sources are transparent, and all code is open for inspection.
          </p>
          <p>
            We adhere to strict factual accuracy. Events must be supported by credible 
            sources including court documents, official records, verified reporting from 
            established outlets, or direct documentation.
          </p>
          <p className="license-info">
            <strong>Data:</strong> CC BY-SA 4.0 | <strong>Code:</strong> MIT License
          </p>
        </section>

        <footer className="landing-footer">
          <button className="enter-timeline-btn-bottom" onClick={onEnterTimeline}>
            Explore the Timeline →
          </button>
          <p className="footer-tagline">
            "Those who would destroy democracy depend on our ignorance. This timeline is our defense."
          </p>
        </footer>
      </div>
    </div>
  );
};

export default LandingPage;