import React from 'react';
import { BookOpen, Network, Tag, FileText, Quote, MessageSquare, Search } from 'lucide-react';

const StartHere = ({ onViewChange }) => {
  const features = [
    {
      icon: BookOpen,
      title: "Topics",
      description: "Explore organized thoughts and ideas by topic",
      color: "bg-purple-100 text-purple-800 border-purple-300",
      action: () => onViewChange('topics')
    },
    {
      icon: MessageSquare,
      title: "Thoughts",
      description: "Personal insights and reflections",
      color: "bg-green-100 text-green-800 border-green-300",
      action: () => onViewChange('thoughts')
    },
    {
      icon: Quote,
      title: "Quotes",
      description: "Meaningful quotes from various sources",
      color: "bg-yellow-100 text-yellow-800 border-yellow-300",
      action: () => onViewChange('quotes')
    },
    {
      icon: FileText,
      title: "Passages",
      description: "Scripture passages and biblical references",
      color: "bg-blue-100 text-blue-800 border-blue-300",
      action: () => onViewChange('passages')
    },
    {
      icon: Network,
      title: "Graph View",
      description: "Interactive visualization of connections",
      color: "bg-indigo-100 text-indigo-800 border-indigo-300",
      action: () => window.open('http://localhost:8000/graph/', '_blank')
    },
    {
      icon: Tag,
      title: "Tags",
      description: "Browse content by tags and categories",
      color: "bg-gray-100 text-gray-800 border-gray-300",
      action: () => onViewChange('tags')
    }
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          Book of Thoughts
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          A personal knowledge base for organizing thoughts, quotes, passages, and insights. 
          Explore connections between ideas through an interactive graph visualization.
        </p>
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => window.open('http://localhost:8000/graph/', '_blank')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Explore Graph
          </button>
          <button
            onClick={() => onViewChange('topics')}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Browse Topics
          </button>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <div
              key={index}
              onClick={feature.action}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-center mb-4">
                <div className={`p-2 rounded-lg ${feature.color} mr-3`}>
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">{feature.title}</h3>
              </div>
              <p className="text-gray-600 text-sm">{feature.description}</p>
            </div>
          );
        })}
      </div>

      {/* About Section */}
      <div className="bg-gray-50 rounded-lg p-8 mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">About This Collection</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">The Tables</h3>
            <p className="text-gray-600 mb-4">
              Organized collections of thoughts, quotes, and passages structured by topics and themes.
            </p>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">The Tags</h3>
            <p className="text-gray-600">
              Cross-referencing system to find related content across different categories.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Graph Visualization</h3>
            <p className="text-gray-600 mb-4">
              Interactive network showing relationships between ideas, topics, and content.
            </p>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Search & Discovery</h3>
            <p className="text-gray-600">
              Full-text search across all content to find specific ideas and connections.
            </p>
          </div>
        </div>
      </div>

      {/* Getting Started */}
      <div className="bg-blue-50 rounded-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Getting Started</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="bg-blue-100 rounded-full p-3 w-12 h-12 mx-auto mb-3 flex items-center justify-center">
              <span className="text-blue-600 font-bold">1</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Start with Topics</h3>
            <p className="text-gray-600 text-sm">Browse the main topics to get an overview of the content structure.</p>
          </div>
          <div className="text-center">
            <div className="bg-blue-100 rounded-full p-3 w-12 h-12 mx-auto mb-3 flex items-center justify-center">
              <span className="text-blue-600 font-bold">2</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Explore the Graph</h3>
            <p className="text-gray-600 text-sm">Visualize connections between different ideas and concepts.</p>
          </div>
          <div className="text-center">
            <div className="bg-blue-100 rounded-full p-3 w-12 h-12 mx-auto mb-3 flex items-center justify-center">
              <span className="text-blue-600 font-bold">3</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Search & Discover</h3>
            <p className="text-gray-600 text-sm">Use the search functionality to find specific content and ideas.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StartHere;