import React, { useState, useEffect } from 'react';
import { BookOpen, Search, Filter, TreePine, ExternalLink, Tag, ChevronRight, ChevronDown } from 'lucide-react';

const TopicsView = ({ api }) => {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'hierarchy'
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [stats, setStats] = useState(null);

  // Fetch topics data
  useEffect(() => {
    fetchTopics();
    fetchStats();
  }, [searchTerm, levelFilter]);

  const fetchTopics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let endpoint = '/topics/api/';
      const params = new URLSearchParams();
      
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      if (levelFilter !== 'all') {
        params.append('level', levelFilter);
      }
      
      if (params.toString()) {
        endpoint += '?' + params.toString();
      }
      
      const response = await fetch(`http://localhost:8000${endpoint}`);
      if (!response.ok) throw new Error('Failed to fetch topics');
      
      const data = await response.json();
      setTopics(data.results || []);
    } catch (err) {
      setError(err.message);
      console.error('Topics fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/topics/api/stats/');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Stats fetch error:', err);
    }
  };

  const toggleNode = (nodeId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const renderTableView = () => (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200 rounded-lg">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Level
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Title
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Description
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tags
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {topics.map((topic, index) => (
            <tr key={topic.id || index} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  L{topic.level || 0}
                </span>
              </td>
              <td className="px-6 py-4">
                <div className="text-sm font-medium text-gray-900">
                  {topic.display_title || topic.title || 'Untitled'}
                </div>
              </td>
              <td className="px-6 py-4">
                <div className="text-sm text-gray-600 max-w-xs truncate">
                  {topic.short_description || topic.description || 'No description'}
                </div>
              </td>
              <td className="px-6 py-4">
                <div className="flex flex-wrap gap-1">
                  {topic.tags && topic.tags.length > 0 ? (
                    topic.tags.slice(0, 3).map((tag, tagIndex) => (
                      <span
                        key={tagIndex}
                        className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800"
                      >
                        <Tag className="w-3 h-3 mr-1" />
                        {tag}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-400 text-xs">No tags</span>
                  )}
                  {topic.tags && topic.tags.length > 3 && (
                    <span className="text-xs text-gray-500">
                      +{topic.tags.length - 3} more
                    </span>
                  )}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <a
                  href={`http://localhost:8000/topics/topic/${topic.id}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-blue-600 hover:text-blue-900"
                >
                  View Details
                  <ExternalLink className="w-4 h-4 ml-1" />
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderHierarchyView = () => {
    // Group topics by level for hierarchy display
    const topicsByLevel = topics.reduce((acc, topic) => {
      const level = topic.level || 0;
      if (!acc[level]) acc[level] = [];
      acc[level].push(topic);
      return acc;
    }, {});

    const levels = Object.keys(topicsByLevel).sort((a, b) => parseInt(a) - parseInt(b));

    return (
      <div className="space-y-4">
        {levels.map(level => (
          <div key={level} className="border border-gray-200 rounded-lg">
            <div
              className="px-4 py-3 bg-gray-50 cursor-pointer flex items-center justify-between"
              onClick={() => toggleNode(`level-${level}`)}
            >
              <div className="flex items-center">
                {expandedNodes.has(`level-${level}`) ? (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-500" />
                )}
                <span className="ml-2 font-medium text-gray-900">
                  Level {level} ({topicsByLevel[level].length} topics)
                </span>
              </div>
            </div>
            
            {expandedNodes.has(`level-${level}`) && (
              <div className="p-4 space-y-2">
                {topicsByLevel[level].map((topic, index) => (
                  <div
                    key={topic.id || index}
                    className="flex items-center justify-between p-3 bg-white border border-gray-100 rounded hover:bg-gray-50"
                  >
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">
                        {topic.display_title || topic.title || 'Untitled'}
                      </h4>
                      {topic.short_description && (
                        <p className="text-sm text-gray-600 mt-1">
                          {topic.short_description}
                        </p>
                      )}
                      {topic.tags && topic.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {topic.tags.slice(0, 5).map((tag, tagIndex) => (
                            <span
                              key={tagIndex}
                              className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <a
                      href={`http://localhost:8000/topics/topic/${topic.id}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-4 inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200"
                    >
                      View
                      <ExternalLink className="w-4 h-4 ml-1" />
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading topics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-2">⚠️ Error</div>
        <p className="text-gray-600">{error}</p>
        <button
          onClick={fetchTopics}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Topics</h2>
          <div className="flex space-x-2">
            <a
              href="http://localhost:8000/topics/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Advanced Features
              <ExternalLink className="w-4 h-4 ml-1" />
            </a>
          </div>
        </div>
        
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>💡 Tip:</strong> This is the embedded Topics view. For advanced features like detailed search, 
            hierarchy management, and administrative tools, use the "Advanced Features" link above.
          </p>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.total_topics}</div>
              <div className="text-sm text-blue-600">Total Topics</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {Object.keys(stats.level_distribution || {}).length}
              </div>
              <div className="text-sm text-green-600">Hierarchy Levels</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {(stats.top_tags || []).length}
              </div>
              <div className="text-sm text-purple-600">Unique Tags</div>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {topics.length}
              </div>
              <div className="text-sm text-yellow-600">Current View</div>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search topics..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Levels</option>
              {stats && Object.keys(stats.level_distribution || {}).map(level => (
                <option key={level} value={level}>
                  Level {level} ({stats.level_distribution[level]})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-2 text-sm font-medium rounded-md ${
                viewMode === 'table'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Table
            </button>
            <button
              onClick={() => setViewMode('hierarchy')}
              className={`px-3 py-2 text-sm font-medium rounded-md ${
                viewMode === 'hierarchy'
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <TreePine className="w-4 h-4 mr-1 inline" />
              Hierarchy
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow">
        {topics.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No topics found</h3>
            <p className="text-gray-600">
              {searchTerm || levelFilter !== 'all'
                ? 'Try adjusting your search or filter criteria.'
                : 'No topics are available yet.'}
            </p>
          </div>
        ) : (
          <div className="p-6">
            {viewMode === 'table' ? renderTableView() : renderHierarchyView()}
          </div>
        )}
      </div>
    </div>
  );
};

export default TopicsView;