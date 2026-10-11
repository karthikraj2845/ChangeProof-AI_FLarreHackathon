import React, { useEffect, useState, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Network,
  Info,
  Maximize2,
  TrendingUp,
  Layers,
  Shield,
  FileCheck,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { CustomInsuranceNode } from '../../components/CustomNode';

const nodeTypes = {
  customInsuranceNode: CustomInsuranceNode,
};

export const ImpactAnalysisPage: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const loadGraph = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getGraph();
      setNodes(data.nodes);
      setEdges(data.edges);

      // Default select the proposed rule version node
      if (data.nodes.length > 0) {
        const defaultNode = data.nodes.find((n: any) => n.id === 'ART-VER-1.1') || data.nodes[0];
        loadArtifactDetails(defaultNode.id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadArtifactDetails = async (id: string) => {
    try {
      const details = await apiClient.getArtifactDetails(id);
      setSelectedArtifact(details);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadGraph();
  }, []);

  const onNodeClick = useCallback((event: any, node: any) => {
    loadArtifactDetails(node.id);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight flex items-center">
            <Network className="w-6 h-6 mr-2 text-sky-400" />
            RuleRipple Dependency Graph
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Authoritative NetworkX insurance dependency architecture with reachability traversal and multi-factor scoring.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
            {nodes.length} Nodes &bull; {edges.length} Edges
          </span>
        </div>
      </div>

      {/* Main Grid: Flow Canvas on left, Deep Inspector on right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[650px]">
        {/* React Flow Canvas (2 cols) */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden relative shadow-2xl">
          {loading ? (
            <div className="flex items-center justify-center h-full text-slate-400">
              Loading NetworkX graph topology...
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              nodeTypes={nodeTypes}
              fitView
              minZoom={0.2}
              maxZoom={1.5}
            >
              <Background color="#1e293b" gap={20} size={1} />
              <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300 fill-slate-300" />
              <MiniMap
                nodeColor="#0284c7"
                maskColor="rgba(15, 23, 42, 0.7)"
                className="!bg-slate-950 !border-slate-800 rounded-lg overflow-hidden"
              />
            </ReactFlow>
          )}
          <div className="absolute bottom-4 left-4 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-lg text-[11px] font-mono text-slate-400 pointer-events-none">
            Click any artifact node to inspect blast radius & impact score
          </div>
        </div>

        {/* Deep Inspector Drawer (1 col) */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 overflow-y-auto space-y-5">
          {selectedArtifact ? (
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
                    {selectedArtifact.artifact?.artifact_type}
                  </span>
                  <span className="text-xs font-mono text-slate-400">
                    v{selectedArtifact.artifact?.version}
                  </span>
                </div>
                <h3 className="text-base font-bold text-white mt-1">
                  {selectedArtifact.artifact?.name}
                </h3>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  {selectedArtifact.artifact?.description}
                </p>
              </div>

              {/* Explainable Impact Score Card */}
              <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/80 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
                    Explainable Impact Score
                  </span>
                  <span className="text-xl font-extrabold font-mono text-amber-400">
                    {selectedArtifact.impact_score_breakdown?.total_score}
                    <span className="text-xs text-slate-400 font-normal"> / 100</span>
                  </span>
                </div>

                {/* Score Factor Breakdown */}
                <div className="space-y-2 text-xs font-mono pt-2 border-t border-slate-800">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Blast Radius Reach (35%):</span>
                    <span className="text-slate-200">
                      {((selectedArtifact.impact_score_breakdown?.reach_factor ?? 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Business Criticality (35%):</span>
                    <span className="text-slate-200">
                      {((selectedArtifact.impact_score_breakdown?.criticality_factor ?? 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Change Proximity (20%):</span>
                    <span className="text-slate-200">
                      {((selectedArtifact.impact_score_breakdown?.proximity_factor ?? 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Uncertainty Penalty (10%):</span>
                    <span className="text-slate-200">
                      {((selectedArtifact.impact_score_breakdown?.uncertainty_factor ?? 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <p className="text-[11px] text-slate-400 italic pt-1">
                  *Score serves as an objective prioritization aid, not a calibrated failure probability.
                </p>
              </div>

              {/* Downstream Blast Radius List */}
              <div className="space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
                  Downstream Blast Radius ({selectedArtifact.downstream_impacted_count})
                </span>
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {(selectedArtifact.downstream_artifacts || []).map((down: any) => (
                    <div
                      key={down.artifact_id}
                      className="p-2.5 rounded-lg border border-slate-800 bg-slate-950/60 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between font-semibold text-slate-200">
                        <span className="truncate">{down.name}</span>
                        <span className="text-[10px] font-mono text-amber-400 shrink-0 ml-2">
                          Score: {down.impact_score}
                        </span>
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 truncate">
                        Edge: {down.relationship_type} &bull; via {down.evidence_source}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-16 text-slate-400 text-xs">
              Select an artifact node on the canvas to inspect its dependency path and impact metrics.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
