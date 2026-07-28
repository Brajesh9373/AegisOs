import React, { useState } from 'react';
import { UniversalConnector } from '@aegisos/contracts';
import { ConnectorCenterDTO } from '../index';

export interface ConnectorCenterProps {
  initialState: ConnectorCenterDTO;
  onSync: (connectorId: string) => Promise<void>;
  onViewLogs: (connectorId: string) => void;
}

export function ConnectorCenter({ initialState, onSync, onViewLogs }: ConnectorCenterProps) {
  const [state] = useState<ConnectorCenterDTO>(initialState);
  const [selectedConnector, setSelectedConnector] = useState<UniversalConnector | null>(null);

  const handleSync = async (id: string) => {
    await onSync(id);
    // In a real app, this would refresh the state
  };

  return (
    <div className="connector-center">
      <h1>Connector Center</h1>

      <div className="health-dashboard">
        <h2>Health Metrics</h2>
        <ul>
          {Object.entries(state.healthMetrics).map(([key, value]) => (
            <li key={key}>
              {key}: {value}%
            </li>
          ))}
        </ul>
      </div>

      <div className="connector-layout" style={{ display: 'flex', gap: '2rem' }}>
        <div className="connector-list" style={{ flex: 1 }}>
          <h2>Installed Connectors</h2>
          <ul>
            {state.installedConnectors.map((connector) => (
              <li
                key={connector.id}
                style={{ marginBottom: '1rem', border: '1px solid #ccc', padding: '1rem' }}
              >
                <h3>
                  {connector.name} v{connector.version}
                </h3>
                <p>Status: {connector.state}</p>
                <button onClick={() => setSelectedConnector(connector)}>View Details</button>
                <button onClick={() => handleSync(connector.id)}>Trigger Sync</button>
                <button onClick={() => onViewLogs(connector.id)}>View Logs</button>
              </li>
            ))}
          </ul>
        </div>

        <div className="connector-details" style={{ flex: 1 }}>
          <h2>Connector Details</h2>
          {selectedConnector ? (
            <div>
              <h3>{selectedConnector.name}</h3>
              <p>ID: {selectedConnector.id}</p>
              <p>Type: {selectedConnector.state}</p>
              <p>Version: {selectedConnector.version}</p>
              <p>Supported Modalities: {selectedConnector.supportedModalities.join(', ')}</p>

              <h4>Active Sync Jobs</h4>
              <ul>
                {state.syncJobs
                  .filter((job) => job.skillId === selectedConnector.id)
                  .map((job) => (
                    <li key={job.id}>
                      {job.id} - {job.status}
                    </li>
                  ))}
              </ul>
            </div>
          ) : (
            <p>Select a connector to view details.</p>
          )}
        </div>
      </div>
    </div>
  );
}
