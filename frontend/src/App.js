import React, { useState, useEffect } from 'react';
import { Search, BookOpen, MessageSquare, Quote, FileText, Tag, Clock, Network, Menu, X } from 'lucide-react';
import StartHere from './StartHere';
import GraphView from './GraphView';

// API base URL
const API_BASE_URL = 'http://localhost:8000/api';

// API service
const api = {
  get: async (endpoint) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) throw new Error('API request failed');
    return response.json();
  }
};

// Color mapping for different content types
const typeColors = {
  Topic: 'bg-purple-100 text-purple-800 border-purple-300',
  Thought: 'bg-green-100 text-green-800 border-green-300',
  Quote: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  Passage: 'bg-blue-100 text-blue-800 border-blue-300'
};

const typeIcons = {
  Topic: BookOpen,
  Thought: MessageSquare,
  Quote: Quote,
  Passage: FileText
};

// Header Component
const Header = ({ onMenuToggle, searchTerm, onSearchChange, onSearch }) => (
  <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between h-16">
        <div className="flex items-center">
          <button
            onClick={onMenuToggle}
            className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 lg:hidden"
          >
            <Menu className="h-6 w-6" />
          </button>
          <h1 className="ml-2 text-2xl font-bold text-gray-900">Book of Thoughts</h1>
        </div>
        
        <div className="flex-1 max-w-md mx-8">
          <div className="relative">
            <input
              type="text"
              placeholder="Search thoughts, topics, quotes..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && onSearch()}
            />
            <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
          </div>
        </div>
      </div>
    </div>
  </header>
);

// Sidebar Component
const Sidebar = ({ isOpen, onClose, activeView, onViewChange }) => {
  const navigation = [
    { name: 'Start Here', id: 'start', icon: BookOpen },
    { name: 'Graph', id: 'graph', icon: Network },
    { name: 'Topics', id: 'topics', icon: BookOpen },
    { name: 'Topics View', id: 'topics-view', icon: BookOpen, isExternal: true, url: 'http://localhost:8000/topics/' },
    { name: 'Thoughts', id: 'thoughts', icon: MessageSquare },
    { name: 'Quotes', id: 'quotes', icon: Quote },
    { name: 'Passages', id: 'passages', icon: FileText },
    { name: 'Tags', id: 'tags', icon: Tag },
  ];

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-25 z-40 lg:hidden" onClick={onClose} />
      )}
      
      <div className={`fixed left-0 top-0 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out z-50 lg:relative lg:translate-x-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-between p-4 border-b lg:hidden">
          <h2 className="text-lg font-semibold">Navigation</h2>
          <button onClick={onClose} className="p-1 rounded-md hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <nav className="mt-4 lg:mt-8">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (item.isExternal && item.url) {
                    window.open(item.url, '_blank');
                  } else {
                    onViewChange(item.id);
                  }
                  onClose();
                }}
                className={`w-full flex items-center px-4 py-3 text-left hover:bg-gray-50 transition-colors ${
                  activeView === item.id ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700' : 'text-gray-700'
                }`}
              >
                <Icon className="h-5 w-5 mr-3" />
                {item.name}
              </button>
            );
          })}
        </nav>
      </div>
    </>
  );
};

// Content Card Component
const ContentCard = ({ item, onClick }) => {
  const TypeIcon = typeIcons[item.type] || MessageSquare;
  
  return (
    <div 
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onClick(item)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center">
          <TypeIcon className="h-5 w-5 mr-2 text-gray-500" />
          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${typeColors[item.type]}`}>
            {item.type}
          </span>
        </div>
        {item.last_modified && (
          <span className="text-xs text-gray-500">
            {new Date(item.last_modified).toLocaleDateString()}
          </span>
        )}
      </div>
      
      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{item.title}</h3>
      
      {item.content && (
        <p className="text-gray-600 text-sm line-clamp-3 mb-3">{item.content}</p>
      )}
      
      {item.author && (
        <p className="text-gray-500 text-sm italic">— {item.author}</p>
      )}
      
      {item.tags && item.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {item.tags.slice(0, 3).map((tag, index) => (
            <span key={index} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
              #{tag}
            </span>
          ))}
          {item.tags.length > 3 && (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
              +{item.tags.length - 3} more
            </span>
          )}
        </div>
      )}
    </div>
  );
};

// Loading Component
const Loading = () => (
  <div className="flex items-center justify-center py-12">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
  </div>
);

// Error Component
const ErrorMessage = ({ message }) => (
  <div className="text-center py-12">
    <div className="text-red-600 mb-2">⚠️ Error</div>
    <p className="text-gray-600">{message}</p>
  </div>
);

// Main Content Area
const ContentArea = ({ activeView, searchResults, onItemClick, searchTerm, onViewChange }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (activeView === 'search' && searchResults) {
      setData(searchResults);
      return;
    }

    const fetchData = async () => {
      if (activeView === 'graph' || activeView === 'start') return; // Graph and Start views handled separately
      
      setLoading(true);
      setError(null);
      
      try {
        let endpoint = '';
        switch (activeView) {
          case 'start': endpoint = '/topics/'; break;
          case 'topics': endpoint = '/topics/'; break;
          case 'thoughts': endpoint = '/thoughts/'; break;
          case 'quotes': endpoint = '/quotes/'; break;
          case 'passages': endpoint = '/passages/'; break;
          case 'tags': endpoint = '/tags/'; break;
          default: endpoint = '/topics/';
        }
        
        const response = await api.get(`${endpoint}?page=${page}`);
        setData(response.results || []);
      } catch (err) {
        setError('Failed to load data. Please try again.');
        console.error('Fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeView, page]);

  const renderContent = () => {
    if (activeView === 'start') {
      return <StartHere onViewChange={onViewChange} />;
    }
    
    if (activeView === 'graph') {
      return <GraphView api={api} />;
    }
    
    if (loading) return <Loading />;
    if (error) return <ErrorMessage message={error} />;
    
    if (activeView === 'tags') {
      return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {data.map((tag, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">#{tag.name}</span>
                <span className="text-sm text-gray-500">{tag.usage_count}</span>
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (!data.length) {
      return (
        <div className="text-center py-12">
          <BookOpen className="h-16 w-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No content found</h3>
          <p className="text-gray-600">
            {searchTerm ? `No results found for "${searchTerm}"` : 'No content available in this section.'}
          </p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data.map((item, index) => (
          <ContentCard key={index} item={item} onClick={onItemClick} />
        ))}
      </div>
    );
  };

  return (
    <div className="flex-1 p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 capitalize">
          {activeView === 'search' ? `Search Results for "${searchTerm}"` : activeView}
        </h2>
        {data.length > 0 && (
          <p className="text-gray-600 mt-1">{data.length} items found</p>
        )}
      </div>
      
      {renderContent()}
    </div>
  );
};

// Item Detail Modal
const ItemDetailModal = ({ item, onClose }) => {
  if (!item) return null;
  
  const TypeIcon = typeIcons[item.type] || MessageSquare;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center">
              <TypeIcon className="h-6 w-6 mr-2 text-gray-500" />
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${typeColors[item.type]}`}>
                {item.type}
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-md hover:bg-gray-100"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          
          <h2 className="text-2xl font-bold text-gray-900 mb-4">{item.title}</h2>
          
          {item.content && (
            <div className="prose max-w-none mb-6">
              <p className="text-gray-700 whitespace-pre-line">{item.content}</p>
            </div>
          )}
          
          {item.author && (
            <p className="text-gray-600 italic mb-4">— {item.author}</p>
          )}
          
          {item.book && (
            <p className="text-gray-600 mb-4">
              {item.book} {item.chapter}:{item.verse}
            </p>
          )}
          
          {item.tags && item.tags.length > 0 && (
            <div className="mb-4">
              <h4 className="font-medium text-gray-900 mb-2">Tags:</h4>
              <div className="flex flex-wrap gap-2">
                {item.tags.map((tag, index) => (
                  <span key={index} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {item.last_modified && (
            <p className="text-sm text-gray-500">
              Last modified: {new Date(item.last_modified).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// Main App Component
export default function BookOfThoughtsApp() {
  const [activeView, setActiveView] = useState('start');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;
    
    setLoading(true);
    try {
      const response = await api.get(`/search/?q=${encodeURIComponent(searchTerm)}`);
      setSearchResults(response.results || []);
      setActiveView('search');
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewChange = (view) => {
    setActiveView(view);
    if (view !== 'search') {
      setSearchResults(null);
      setSearchTerm('');
    }
  };

  const handleItemClick = (item) => {
    setSelectedItem(item);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        onMenuToggle={() => setSidebarOpen(true)}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onSearch={handleSearch}
      />
      
      <div className="flex">
        <Sidebar 
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          activeView={activeView}
          onViewChange={handleViewChange}
        />
        
        <ContentArea 
          activeView={activeView}
          searchResults={searchResults}
          onItemClick={handleItemClick}
          searchTerm={searchTerm}
          onViewChange={handleViewChange}
        />
      </div>
      
      {selectedItem && (
        <ItemDetailModal 
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}
    </div>
  );
}