import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const GraphView = ({ api }) => {
  const svgRef = useRef();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  console.log('GraphView rendered, api:', api, 'loading:', loading, 'error:', error, 'nodes:', graphData.nodes.length);

  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8000/graph/api/data/');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Graph data received:', data);
        
        if (!data.nodes || !data.links) {
          throw new Error('Invalid graph data structure');
        }
        
        setGraphData(data);
      } catch (err) {
        setError(`Failed to load graph data: ${err.message}`);
        console.error('Graph data fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, [api]);

  useEffect(() => {
    if (loading || error || !graphData.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 800;
    const height = 600;

    svg
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])
      .style("max-width", "100%")
      .style("height", "auto");

    // Color scale for different node types
    const colorScale = d3.scaleOrdinal()
      .domain(['Topic', 'Thought', 'Quote', 'Passage'])
      .range(['#8B5CF6', '#10B981', '#F59E0B', '#3B82F6']);

    // Create simulation
    const simulation = d3.forceSimulation(graphData.nodes)
      .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

    // Create links
    const link = svg.append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(graphData.links)
      .join("line")
      .attr("stroke-width", d => Math.sqrt(d.value || 1));

    // Create nodes
    const node = svg.append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll("circle")
      .data(graphData.nodes)
      .join("circle")
      .attr("r", d => Math.sqrt((d.size || 10) * 3))
      .attr("fill", d => colorScale(d.type))
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    // Add labels
    const label = svg.append("g")
      .selectAll("text")
      .data(graphData.nodes)
      .join("text")
      .text(d => d.title || d.name || d.id || 'Unknown')
      .style("font-size", "12px")
      .style("font-family", "Arial, sans-serif")
      .style("fill", "#333")
      .style("text-anchor", "middle")
      .style("dominant-baseline", "central")
      .style("pointer-events", "none");

    // Add tooltips
    node.append("title")
      .text(d => `${d.type}: ${d.title || d.name || d.id || 'Unknown'}${d.tags ? `\nTags: ${d.tags.join(', ')}` : ''}`);

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);

      label
        .attr("x", d => d.x)
        .attr("y", d => d.y + 25);
    });

    // Drag functions
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return () => {
      simulation.stop();
    };

  }, [graphData, loading, error]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading graph data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️ Error</div>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Knowledge Graph</h3>
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span>Nodes: {graphData.nodes.length}</span>
          <span>Connections: {graphData.links.length}</span>
        </div>
        <div className="flex items-center space-x-4 mt-2">
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-purple-500 mr-1"></div>
            <span className="text-xs">Topics</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-1"></div>
            <span className="text-xs">Thoughts</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-yellow-500 mr-1"></div>
            <span className="text-xs">Quotes</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-blue-500 mr-1"></div>  
            <span className="text-xs">Passages</span>
          </div>
        </div>
      </div>
      
      <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
        <svg ref={svgRef} className="w-full"></svg>
      </div>
      
      <div className="mt-2 text-xs text-gray-500">
        Drag nodes to rearrange • Hover for details
      </div>
    </div>
  );
};

export default GraphView;