'use client';

import React, { useState, useRef, useEffect } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  Loader2, 
  Download, 
  Settings 
} from 'lucide-react';

export default function Home() {
  // Config States
  const [backendUrl, setBackendUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  );
  const [targetVariable, setTargetVariable] = useState('purchased');
  const [taskType, setTaskType] = useState('classification');
  const [selectedModel, setSelectedModel] = useState('Random Forest');
  const [minThreshold, setMinThreshold] = useState(0.90);
  const [showConfig, setShowConfig] = useState(false);

  // Dynamic CSV columns list
  const [columns, setColumns] = useState([]);

  // File States
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Pipeline States
  const [status, setStatus] = useState('idle'); // idle | running | success | error
  const [logs, setLogs] = useState([]);
  const [rawResponse, setRawResponse] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);

  // Dynamic models dropdown list based on taskType
  const classificationModels = [
    "Logistic Regression",
    "Decision Tree",
    "Random Forest",
    "XGBoost",
    "LightGBM",
    "CatBoost",
    "Support Vector Machine (SVM)",
    "K-Nearest Neighbors",
    "Naive Bayes"
  ];

  const regressionModels = [
    "Linear Regression",
    "Decision Tree",
    "Random Forest",
    "XGBoost",
    "LightGBM",
    "CatBoost",
    "Support Vector Machine (SVR)",
    "K-Nearest Neighbors"
  ];

  const currentModels = taskType === 'classification' ? classificationModels : regressionModels;

  // Set default model on taskType change
  useEffect(() => {
    setSelectedModel(currentModels[2] || currentModels[0]);
  }, [taskType]);

  // Log Helpers
  const addLog = (text, type = 'stdout') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { type, text: `[${timestamp}] [${type.toUpperCase()}] ${text}` }]);
  };

  const appendRawLog = (rawLogStr) => {
    // Parse db log formats
    let type = 'info';
    if (rawLogStr.includes('[OK]')) type = 'ok';
    else if (rawLogStr.includes('[ERR]') || rawLogStr.includes('[ERROR]')) type = 'err';
    else if (rawLogStr.includes('[SYSTEM]')) type = 'info';
    else if (rawLogStr.includes('[WARN]')) type = 'warn';
    else if (rawLogStr.includes('[AGENT]')) type = 'agent';

    const text = rawLogStr
      .replace(/\[OK\]\s*/, '')
      .replace(/\[ERR\]\s*/, '')
      .replace(/\[ERROR\]\s*/, '')
      .replace(/\[SYSTEM\]\s*/, '')
      .replace(/\[AGENT\]\s*/, '')
      .replace(/\[WARN\]\s*/, '');

    // Extract timestamp
    const timeMatch = text.match(/^\[(\d{2}:\d{2}:\d{2})\]\s*/);
    const ts = timeMatch ? timeMatch[1] : new Date().toLocaleTimeString();
    const cleanMsg = text.replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '');

    setLogs(prev => [...prev, { ts, tag: type, msg: cleanMsg }]);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      processFile(droppedFile);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      processFile(selectedFile);
    }
  };

  const processFile = (selectedFile) => {
    if (selectedFile.name.endsWith('.csv') || selectedFile.name.endsWith('.xlsx')) {
      setFile(selectedFile);
      setLogs([]);
      
      // Local check: Boot log
      setLogs([{ ts: new Date().toLocaleTimeString(), tag: 'info', msg: `Selected dataset file: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)` }]);

      // Parse columns locally from CSV to prefill Target Variable picker
      if (selectedFile.name.endsWith('.csv')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            const text = event.target.result;
            const firstLine = text.split('\n')[0];
            const cols = firstLine.split(',').map(c => c.trim().replace(/^"|"$/g, ''));
            if (cols.length > 0 && cols[0] !== '') {
              setColumns(cols);
              setTargetVariable(cols[cols.length - 1]); // Set default target to last column
            }
          } catch (err) {
            console.error("Error reading columns:", err);
          }
        };
        reader.readAsText(selectedFile);
      } else {
        setColumns([]);
      }
    } else {
      setLogs([{ ts: new Date().toLocaleTimeString(), tag: 'err', msg: 'Unsupported file type. Please upload a CSV or Excel file.' }]);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current.click();
  };

  const fillSampleChip = (datasetName, targetCol, typeTask) => {
    setTargetVariable(targetCol);
    setTaskType(typeTask);
    
    // Create a mock File object to enable submission
    const mockFile = new File([""], datasetName, { type: "text/csv" });
    setFile(mockFile);
    setColumns([targetCol, "feature1", "feature2", "feature3"]);
    
    setLogs([{ 
      ts: new Date().toLocaleTimeString(), 
      tag: 'info', 
      msg: `Loaded sample config for ${datasetName}. Drag & drop the real file or click Run to trigger execution.` 
    }]);
  };

  const executePipeline = async () => {
    if (!file) return;

    setStatus('running');
    setLogs([]);
    setRawResponse(null);
    setDownloadUrl(null);

    const timeStart = new Date().toLocaleTimeString();
    setLogs([
      { ts: timeStart, tag: 'info', msg: 'Trigger received from operator.' },
      { ts: timeStart, tag: 'agent', msg: `Payload prepared → dataset='${file.name}', target='${targetVariable}', task='${taskType}', model='${selectedModel}', min_threshold=${minThreshold}` },
      { ts: timeStart, tag: 'info', msg: `POST → ${backendUrl}/api/upload` }
    ]);

    try {
      const formData = new FormData();
      // If mock file, create a tiny empty payload, else use actual file content
      formData.append('file', file);
      formData.append('target_variable', targetVariable);
      formData.append('task_type', taskType);
      formData.append('selected_model', selectedModel);
      formData.append('min_threshold', minThreshold.toString());

      // 1. Upload file metadata
      const uploadRes = await fetch(`${backendUrl}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadRes.ok) {
        throw new Error(`Upload failed with status: ${uploadRes.status}`);
      }

      const { run_id } = await uploadRes.json();
      appendRawLog(`[OK] Dataset successfully ingested. Initialized Run ID: ${run_id}`);

      // 2. Trigger run execution
      appendRawLog(`[SYSTEM] Triggering pipeline orchestrator thread...`);
      const triggerRes = await fetch(`${backendUrl}/api/runs/${run_id}/trigger`, {
        method: 'POST',
      });

      if (!triggerRes.ok) {
        throw new Error(`Trigger failed with status: ${triggerRes.status}`);
      }

      appendRawLog(`[SYSTEM] Pipeline orchestrator running. Commencing live telemetry polling...`);

      // 3. Telemetry status polling
      let lastLogLength = 0;
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`${backendUrl}/api/runs/${run_id}/status`);
          if (!statusRes.ok) return;

          const data = await statusRes.json();

          // Append new logs sequentially
          if (data.logs && data.logs.length > lastLogLength) {
            const newLogs = data.logs.slice(lastLogLength);
            newLogs.forEach(logStr => appendRawLog(logStr));
            lastLogLength = data.logs.length;
          }

          if (data.status === 'complete' || data.status === 'failed') {
            clearInterval(pollInterval);
            setRawResponse(data);
            if (data.status === 'complete') {
              setStatus('success');
              setDownloadUrl(data.bundle_url || '#');
              appendRawLog('[OK] Pipeline finished successfully. Model bundle produced.');
            } else {
              setStatus('error');
              appendRawLog('[ERR] Pipeline run execution encountered faults.');
            }
          }
        } catch (pollErr) {
          console.error('Polling error:', pollErr);
        }
      }, 1500);

    } catch (err) {
      appendRawLog(`[ERR] Connection failed: ${err.message}`);
      setStatus('error');
    }
  };

  // Node class mapper
  const getNodeClass = (nodeIndex) => {
    if (status === 'success') return '';
    if (status === 'error' && nodeIndex === 2) return 'failed-node'; // Simulate failure at execution sandbox

    const statusMap = {
      'profiling': 0,
      'generating': 1,
      'training': 2,
      'verifying': 3
    };

    const currentActiveIndex = statusMap[status];
    if (status === 'running' && currentActiveIndex === nodeIndex) {
      return 'active';
    }
    return '';
  };

  return (
    <div className="container">
      {/* Brand Nav Header */}
      <div className="brand-row">
        <div className="brand">
          <div className="brand-mark">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 16 L10 4 L14 12 L20 4" stroke="#00E5D1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="10" cy="4" r="1.6" fill="#2C5BFF"/>
              <circle cx="20" cy="4" r="1.6" fill="#2C5BFF"/>
              <path d="M3 20 H21" stroke="#7C4DFF" strokeWidth="1.6" strokeLinecap="round" strokeDasharray="2 3"/>
            </svg>
          </div>
          <div className="brand-name">Auto<span>ML</span></div>
          <div className="brand-tag">Agent · v0.1</div>
        </div>

        <div className="nav-links">
          <a href="#pipeline">Pipeline</a>
          <a href="#how">How it works</a>
          <a href="#config">Configure</a>
          <a href="#logs">Activity</a>
        </div>

        <div className="nav-status">
          <span className="pulse"></span>
          <span>Sandbox online</span>
        </div>
      </div>

      {/* Hero Section */}
      <div className="hero-grid">
        <div>
          <div className="eyebrow"><span className="dot"></span> Autonomous ML Engineer</div>
          <div className="hero-title">Ship models <span className="accent">without writing<br/>the pipeline.</span></div>
          <div className="hero-sub">
            AutoML is an agentic system that profiles your dataset, generates the training
            code, executes it in a sandbox, and self-corrects on failure — until a model bundle
            is ready to download. Point it at a CSV, give it a target column, and step back.
          </div>
          <div className="hero-meta">
            <span><b>◐</b> Profile · Generate · Execute · Self-Correct</span>
            <span><b>◐</b> n8n orchestrated</span>
            <span><b>◐</b> Sandbox isolated</span>
          </div>
        </div>

        <div>
          {/* Animated Pipeline Diagram */}
          <div className="pipe-card" id="pipeline">
            <div className="pipe-card-hd">
              <div className="t">Agent Pipeline</div>
              <div className="k">
                {status === 'idle' && <span style={{ color: 'var(--slate)' }}>◦ IDLE</span>}
                {status === 'running' && <span style={{ color: 'var(--signal)' }}>● RUNNING</span>}
                {status === 'success' && <span style={{ color: 'var(--success)' }}>● SUCCESS</span>}
                {status === 'error' && <span style={{ color: 'var(--rose)' }}>● ERROR</span>}
              </div>
            </div>
            
            <div className={`pipe-diagram ${status}`} style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr auto 1fr auto 1fr', alignItems: 'center' }}>
              
              <div className={`pipe-node ${getNodeClass(0)}`}>
                <div className="ring">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3h7v7H3z"/><path d="M14 3h7v4h-7z"/><path d="M14 10h7v11h-7z"/><path d="M3 14h7v7H3z"/></svg>
                </div>
                <div className="lbl">Profile</div>
                <div className="sub">01 · scan</div>
              </div>

              <div className="pipe-connect">
                <div className="flow"></div>
              </div>

              <div className={`pipe-node ${getNodeClass(1)}`}>
                <div className="ring">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h10l6 6v10H4z"/><path d="M14 4v6h6"/><path d="M8 14h8"/><path d="M8 17h5"/></svg>
                </div>
                <div className="lbl">Generate</div>
                <div className="sub">02 · plan</div>
              </div>

              <div className="pipe-connect">
                <div className="flow"></div>
              </div>

              <div className={`pipe-node ${getNodeClass(2)}`}>
                <div className="ring">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polygon points="6,4 20,12 6,20"/></svg>
                </div>
                <div className="lbl">Execute</div>
                <div className="sub">03 · run</div>
              </div>

              <div className="pipe-connect">
                <div className="flow"></div>
              </div>

              <div className={`pipe-node ${getNodeClass(3)}`}>
                <div className="ring">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 12a8 8 0 0 1 14-5.3"/><path d="M18 4v4h-4"/><path d="M20 12a8 8 0 0 1-14 5.3"/><path d="M6 20v-4h4"/></svg>
                </div>
                <div className="lbl">Self-Correct</div>
                <div className="sub">04 · refine</div>
              </div>

            </div>
          </div>
        </div>
      </div>

      {/* How it Works Section */}
      <div className="section" id="how">
        <div className="lhs">
          <div className="idx">// 01</div>
          <div className="ttl">How the agent thinks</div>
        </div>
        <div className="sub">Four coordinated phases</div>
      </div>

      <div className="hiw-grid">
        <div className="hiw">
          <div className="num">01 / PROFILE</div>
          <div className="ico">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          </div>
          <div className="h">Profile the data</div>
          <div className="p">Scans schema, dtypes, missing rates, cardinality, target balance & leakage risks.</div>
        </div>
        <div className="hiw">
          <div className="num">02 / GENERATE</div>
          <div className="ico">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h10l6 6v10H4z"/><path d="M14 4v6h6"/><path d="M8 14h8"/><path d="M8 17h5"/></svg>
          </div>
          <div className="h">Generate the plan</div>
          <div className="p">LLM writes preprocessing, feature engineering & model code tailored to your dataset.</div>
        </div>
        <div className="hiw">
          <div className="num">03 / EXECUTE</div>
          <div className="ico">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polygon points="6,4 20,12 6,20"/></svg>
          </div>
          <div className="h">Execute in sandbox</div>
          <div className="p">Runs the generated code inside an isolated container via MCP-connected tools.</div>
        </div>
        <div className="hiw">
          <div className="num">04 / SELF-CORRECT</div>
          <div className="ico">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 12a8 8 0 0 1 14-5.3"/><path d="M18 4v4h-4"/><path d="M20 12a8 8 0 0 1-14 5.3"/><path d="M6 20v-4h4"/></svg>
          </div>
          <div className="h">Self-correct on error</div>
          <div className="p">Reads tracebacks, diagnoses the fault, revises the code, retries — until success.</div>
        </div>
      </div>

      {/* Configure Run Section */}
      <div className="section" id="config">
        <div className="lhs">
          <div className="idx">// 02</div>
          <div className="ttl">Configure the run</div>
        </div>
        <div className="sub" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>API Gateway URL & params</span>
          <button 
            onClick={() => setShowConfig(!showConfig)}
            style={{ background: 'transparent', border: 'none', color: 'var(--slate)', cursor: 'pointer' }}
          >
            <Settings size={14} />
          </button>
        </div>
      </div>

      <div className="cfg-card">
        {showConfig && (
          <div style={{ marginBottom: '1.5rem', borderBottom: '1px dashed var(--grid)', paddingBottom: '1.5rem' }}>
            <label className="form-label">API Gateway Host URL</label>
            <input 
              type="text" 
              className="form-input" 
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)} 
            />
          </div>
        )}

        <div className="cfg-grid">
          <div>
            <label className="form-label">Upload Dataset (CSV / Excel)</label>
            <div 
              className={`file-upload-container ${dragActive ? 'active' : ''}`}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={onButtonClick}
            >
              <input 
                ref={fileInputRef}
                type="file" 
                style={{ display: 'none' }} 
                accept=".csv, .xlsx"
                onChange={handleFileChange}
              />
              {file ? (
                <div>
                  <p style={{ fontWeight: '600', color: 'var(--ink)' }}>{file.name}</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--slate)' }}>
                    {(file.size / 1024).toFixed(1)} KB • Click to replace
                  </p>
                </div>
              ) : (
                <div>
                  <p style={{ fontWeight: '600', color: 'var(--ink)' }}>Select dataset file</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--slate)' }}>Drag & drop or click to browse (.csv, .xlsx)</p>
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="form-label">Target Variable</label>
            {columns.length > 0 ? (
              <select 
                className="form-select"
                value={targetVariable}
                onChange={(e) => setTargetVariable(e.target.value)}
              >
                {columns.map(col => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            ) : (
              <input 
                type="text" 
                className="form-input"
                value={targetVariable}
                onChange={(e) => setTargetVariable(e.target.value)}
                placeholder="e.g. purchased"
              />
            )}
          </div>
        </div>

        <div className="cfg-grid">
          <div>
            <label className="form-label">Task Type</label>
            <select 
              className="form-select"
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
            >
              <option value="classification">Classification</option>
              <option value="regression">Regression</option>
            </select>
          </div>

          <div>
            <label className="form-label">Model Selection</label>
            <select 
              className="form-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
            >
              {currentModels.map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label className="form-label">
            Minimum Accuracy/R2 Performance Threshold: {Math.round(minThreshold * 100)}%
          </label>
          <input 
            type="range" 
            className="slider-input" 
            min="50" 
            max="99" 
            value={Math.round(minThreshold * 100)} 
            onChange={(e) => setMinThreshold(parseInt(e.target.value) / 100)} 
          />
        </div>

        {/* Copyable Sample Chips */}
        <div style={{ marginTop: '0.9rem', marginBottom: '1.5rem' }}>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.68rem', letterSpacing: '0.14em', color: 'var(--slate)', textTransform: 'uppercase', marginBottom: '0.45rem' }}>
            Try a sample config
          </div>
          <div className="chips-row">
            <div className="chip signal" onClick={() => fillSampleChip("sample_dataset.csv", "purchased", "classification")}>
              <span className="dot"></span><span className="k">dataset</span><span>sample_dataset.csv</span>
            </div>
            <div className="chip signal" onClick={() => fillSampleChip("titanic.csv", "Survived", "classification")}>
              <span className="dot"></span><span className="k">dataset</span><span>titanic.csv</span>
            </div>
            <div className="chip violet" onClick={() => fillSampleChip("housing.csv", "price", "regression")}>
              <span className="dot"></span><span className="k">dataset</span><span>housing.csv</span>
            </div>
            <div className="chip amber" onClick={() => fillSampleChip("churn.csv", "churned", "classification")}>
              <span className="dot"></span><span className="k">dataset</span><span>churn.csv</span>
            </div>
          </div>
        </div>

        <button 
          className="btn-primary" 
          onClick={executePipeline}
          disabled={!file || status === 'running'}
          style={{ width: '100%' }}
        >
          {status === 'running' ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Triggering Pipeline...
            </>
          ) : (
            "◈ Trigger AutoML Pipeline"
          )}
        </button>
      </div>

      {/* Live Pipeline / Telemetry Log */}
      <div className="section" id="logs">
        <div className="lhs">
          <div className="idx">// 03</div>
          <div className="ttl">Live pipeline</div>
        </div>
        <div className="sub">Agent telemetry stream</div>
      </div>

      <div className="log-card">
        <div className="log-hd">
          <div className="t">Agent Activity</div>
          <div className={`kbd ${status !== 'running' ? 'idle' : ''}`}>
            <span className="live"></span>
            {status === 'running' ? 'LIVE STREAM' : (status === 'idle' ? 'STANDBY' : 'SESSION')}
          </div>
        </div>
        <div className="log-body">
          {logs.length === 0 ? (
            <div className="log-row">
              <span className="ts">--:--:--</span>
              <span className="tag info">boot</span>
              <span className="msg">Waiting for pipeline trigger… <span className="caret">▍</span></span>
            </div>
          ) : (
            <>
              {logs.map((log, idx) => (
                <div key={idx} className="log-row">
                  <span className="ts">{log.ts}</span>
                  <span className="tag tag-class" style={{
                    backgroundColor: log.tag === 'ok' ? 'rgba(16,185,129,0.16)' : (log.tag === 'err' ? 'rgba(244,63,94,0.16)' : (log.tag === 'warn' ? 'rgba(245,158,11,0.16)' : (log.tag === 'agent' ? 'rgba(124,77,255,0.18)' : 'rgba(44,91,255,0.16)'))),
                    color: log.tag === 'ok' ? '#34D8A6' : (log.tag === 'err' ? '#FF7A8E' : (log.tag === 'warn' ? '#FBBF57' : (log.tag === 'agent' ? '#B39BFF' : '#7BA0FF')))
                  }}>
                    {log.tag}
                  </span>
                  <span className="msg" dangerouslySetInnerHTML={{ __html: log.msg }}></span>
                </div>
              ))}
              {status === 'running' && (
                <div className="log-row">
                  <span className="ts">--:--:--</span>
                  <span className="tag info">wait</span>
                  <span className="msg">Streaming agent telemetry… <span className="caret">▍</span></span>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Result Panel */}
      {(status === 'success' || status === 'error') && (
        <>
          <div className="section">
            <div className="lhs">
              <div className="idx">// 04</div>
              <div className="ttl">Result</div>
            </div>
            <div className="sub">{status === 'success' ? 'Model bundle & response' : 'Diagnostics'}</div>
          </div>

          {status === 'success' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '2rem' }}>
              <div className="success-banner">
                <CheckCircle size={20} />
                <span>AutoML pipeline finished successfully!</span>
              </div>
              {downloadUrl && (
                <a href={downloadUrl} className="btn-success">
                  📥 Download AutoML Bundle (.zip)
                </a>
              )}
            </div>
          ) : (
            <div className="error-banner" style={{ marginBottom: '2rem' }}>
              <XCircle size={20} />
              <span>Pipeline did not complete. See agent activity for details.</span>
            </div>
          )}

          {rawResponse && (
            <div style={{ marginBottom: '2rem' }}>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.72rem', letterSpacing: '0.12em', color: 'var(--slate)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Raw response payload
              </div>
              <pre className="json-container">
                {JSON.stringify(rawResponse, null, 2)}
              </pre>
            </div>
          )}
        </>
      )}

      {/* Footer */}
      <div className="foot">
        <div>◈ AutoML · Agentic ML Engineer</div>
        <div>Orchestrated via FastAPI · Executed in sandbox · Corrected by agent</div>
      </div>
    </div>
  );
}
