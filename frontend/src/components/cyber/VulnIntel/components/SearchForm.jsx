/**
 * VULNERABILITY SEARCH FORM - Semantic Form with Radio Group
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <form> with role="search"
 * - <fieldset> + <legend> for search type radio group
 * - role="radiogroup" for search type buttons
 * - <label> associated with input
 * - aria-live for loading status
 *
 * WCAG 2.1 AAA Compliance:
 * - Radio group with proper ARIA
 * - Labeled form controls
 * - Loading status announced
 * - Keyboard accessible
 * - Quick searches as shortcuts
 *
 * @version 2.0.0 (Maximus Vision)
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from 'react';

export const SearchForm = ({ query, setQuery, searchType, setSearchType, onSearch, isLoading }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch();
    }
  };

  const searchTypes = [
    { id: 'cve', name: 'CVE ID', icon: '🔐', placeholder: 'CVE-2024-1234' },
    { id: 'product', name: 'Product', icon: '📦', placeholder: 'Windows Server, Apache' },
    { id: 'vendor', name: 'Vendor', icon: '🏢', placeholder: 'Microsoft, Oracle' },
  ];

  const activeSearchType = searchTypes.find(t => t.id === searchType);

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4"
      role="search"
      aria-label="Vulnerability intelligence search">

      <fieldset>
        <legend className="sr-only">Search Type</legend>
        <div role="radiogroup" aria-label="Search type selection" className="flex gap-2">
          {searchTypes.map(type => (
            <button
              key={type.id}
              type="button"
              role="radio"
              aria-checked={searchType === type.id}
              onClick={() => setSearchType(type.id)}
              aria-label={`Search by ${type.name}`}
              className={`
                px-4 py-2 rounded-lg font-bold text-sm transition-all flex items-center gap-2
                ${
                  searchType === type.id
                    ? 'bg-red-400/20 text-red-400 border-2 border-red-400'
                    : 'bg-black/30 text-red-400/50 border-2 border-red-400/20 hover:text-red-400'
                }
              `}
            >
              <span aria-hidden="true">{type.icon}</span>
              {type.name}
            </button>
          ))}
        </div>
      </fieldset>

      <div className="relative">
        <div className="absolute left-4 top-1/2 transform -translate-y-1/2 text-3xl" aria-hidden="true">
          {activeSearchType?.icon}
        </div>
        <label htmlFor="vuln-search-input" className="sr-only">
          {activeSearchType?.name} Search Query
        </label>
        <input
          id="vuln-search-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={activeSearchType?.placeholder || 'Enter search query...'}
          className="w-full bg-gradient-to-r from-red-900/20 to-pink-900/20 border-2 border-red-400/30 rounded-lg pl-16 pr-32 py-4 text-red-400 font-mono text-lg focus:outline-none focus:border-red-400 transition-all placeholder-red-400/30"
          disabled={isLoading}
          aria-describedby="vuln-search-quick"
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          aria-label="Search for vulnerabilities"
          className="absolute right-2 top-1/2 transform -translate-y-1/2 px-6 py-2 bg-gradient-to-r from-red-600 to-pink-600 text-white font-bold rounded-lg hover:from-red-500 hover:to-pink-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-400/20"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <span className="animate-spin" aria-hidden="true">⚙️</span>
              SEARCHING...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <span aria-hidden="true">🔍</span>
              SEARCH
            </span>
          )}
        </button>
      </div>

      <fieldset id="vuln-search-quick">
        <legend className="text-red-400/50 text-sm">Quick search:</legend>
        <div className="flex items-center gap-2 flex-wrap" role="group" aria-label="Quick search shortcuts">
          {[
            { label: 'CVE-2024-21412', type: 'cve' },
            { label: 'Apache Log4j', type: 'product' },
            { label: 'Microsoft', type: 'vendor' },
          ].map((quick, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setSearchType(quick.type);
                setQuery(quick.label);
              }}
              aria-label={`Quick search: ${quick.label}`}
              className="px-3 py-1 bg-black/30 text-red-400/70 text-xs rounded border border-red-400/20 hover:border-red-400 hover:text-red-400 transition-all"
            >
              {quick.label}
            </button>
          ))}
        </div>
      </fieldset>

      {isLoading && (
        <div className="sr-only" role="status" aria-live="polite">
          Searching for vulnerabilities...
        </div>
      )}
    </form>
  );
};

export default SearchForm;
