import React, { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import './SearchBar.css';

const SearchBar = ({ value, onChange, placeholder }) => {
  const [localValue, setLocalValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localValue);
    }, 300);

    return () => clearTimeout(timer);
  }, [localValue, onChange]);

  return (
    <div className="search-bar">
      <Search className="search-icon" size={18} />
      <input
        type="text"
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        placeholder={placeholder}
        className="search-input"
      />
      {localValue && (
        <button
          className="clear-search"
          onClick={() => {
            setLocalValue('');
            onChange('');
          }}
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
};

export default SearchBar;