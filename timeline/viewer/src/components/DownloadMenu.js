import React, { useState, useRef, useEffect } from 'react';
import { Download, FileText, FileJson, Table, Code } from 'lucide-react';
import './DownloadMenu.css';

function DownloadMenu({ onDownload }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleDownload = (format) => {
    const link = document.createElement('a');
    
    switch (format) {
      case 'csv':
        link.href = process.env.PUBLIC_URL + '/timeline_events.csv';
        link.download = `kleptocracy_timeline_${new Date().toISOString().split('T')[0]}.csv`;
        break;
      case 'json':
        link.href = process.env.PUBLIC_URL + '/timeline_events.json';
        link.download = `kleptocracy_timeline_${new Date().toISOString().split('T')[0]}.json`;
        break;
      case 'yaml':
        link.href = process.env.PUBLIC_URL + '/timeline_events.yaml';
        link.download = `kleptocracy_timeline_${new Date().toISOString().split('T')[0]}.yaml`;
        break;
      case 'yaml-minimal':
        link.href = process.env.PUBLIC_URL + '/timeline_events_minimal.yaml';
        link.download = `kleptocracy_timeline_minimal_${new Date().toISOString().split('T')[0]}.yaml`;
        break;
      default:
        return;
    }
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    if (onDownload) {
      onDownload(format);
    }
    
    setIsOpen(false);
  };

  return (
    <div className="download-menu" ref={menuRef}>
      <button 
        className="icon-button"
        onClick={() => setIsOpen(!isOpen)}
        title="Download timeline data"
      >
        <Download size={20} />
      </button>
      
      {isOpen && (
        <div className="download-dropdown">
          <div className="download-header">Export Timeline Data</div>
          
          <button 
            className="download-option"
            onClick={() => handleDownload('csv')}
          >
            <Table size={16} />
            <div>
              <div className="option-title">CSV Format</div>
              <div className="option-desc">For Excel, Google Sheets, or data analysis</div>
            </div>
          </button>
          
          <button 
            className="download-option"
            onClick={() => handleDownload('json')}
          >
            <FileJson size={16} />
            <div>
              <div className="option-title">JSON Format</div>
              <div className="option-desc">For developers and data processing</div>
            </div>
          </button>
          
          <button 
            className="download-option"
            onClick={() => handleDownload('yaml')}
          >
            <Code size={16} />
            <div>
              <div className="option-title">YAML Format (Full)</div>
              <div className="option-desc">Complete structured data with all fields</div>
            </div>
          </button>
          
          <button 
            className="download-option"
            onClick={() => handleDownload('yaml-minimal')}
          >
            <Code size={16} />
            <div>
              <div className="option-title">YAML Format (Minimal)</div>
              <div className="option-desc">Essential fields only for lighter processing</div>
            </div>
          </button>
          
          <div className="download-footer">
            <FileText size={14} />
            <span>{753} events • Last updated {new Date().toLocaleDateString()}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default DownloadMenu;