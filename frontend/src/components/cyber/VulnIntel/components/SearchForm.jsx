import React from 'react';

/**
 * SearchForm - Formulário de busca de vulnerabilidades
 */
export const SearchForm = ({ query, setQuery, searchType, setSearchType, onSearch, isLoading }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch();
  };

  const searchTypes = [
    { id: 'cve', name: 'CVE ID', icon: '🔐', placeholder: 'CVE-2024-1234' },
    { id: 'product', name: 'Product', icon: '📦', placeholder: 'Windows Server, Apache' },
    { id: 'vendor', name: 'Vendor', icon: '🏢', placeholder: 'Microsoft, Oracle' },
  ];

  const activeSearchType = searchTypes.find(t => t.id === searchType);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Search Type Selection */}
      <div className="flex gap-2">
        {searchTypes.map(type => (
          <button
            key={type.id}
            type="button"
            onClick={() => setSearchType(type.id)}
            className={`
              px-4 py-2 rounded-lg font-bold text-sm transition-all flex items-center gap-2
              ${
                searchType === type.id
                  ? 'bg-red-400/20 text-red-400 border-2 border-red-400'
                  : 'bg-black/30 text-red-400/50 border-2 border-red-400/20 hover:text-red-400'
              }
            `}
          >
            <span>{type.icon}</span>
            {type.name}
          </button>
        ))}
      </div>

      {/* Search Input */}
      <div className="relative">
        <div className="absolute left-4 top-1/2 transform -translate-y-1/2 text-3xl">
          {activeSearchType?.icon}
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={activeSearchType?.placeholder || 'Enter search query...'}
          className="w-full bg-gradient-to-r from-red-900/20 to-pink-900/20 border-2 border-red-400/30 rounded-lg pl-16 pr-32 py-4 text-red-400 font-mono text-lg focus:outline-none focus:border-red-400 transition-all placeholder-red-400/30"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="absolute right-2 top-1/2 transform -translate-y-1/2 px-6 py-2 bg-gradient-to-r from-red-600 to-pink-600 text-white font-bold rounded-lg hover:from-red-500 hover:to-pink-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-400/20"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <span className="animate-spin">⚙️</span>
              SEARCHING...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <span>🔍</span>
              SEARCH
            </span>
          )}
        </button>
      </div>

      {/* Quick Searches */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-red-400/50 text-sm">Quick search:</span>
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
            className="px-3 py-1 bg-black/30 text-red-400/70 text-xs rounded border border-red-400/20 hover:border-red-400 hover:text-red-400 transition-all"
          >
            {quick.label}
          </button>
        ))}
      </div>
    </form>
  );
};

export default SearchForm;
