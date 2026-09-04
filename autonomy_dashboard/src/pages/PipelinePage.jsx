import React, { useState, useCallback } from 'react';
import { useRos } from '../context/RosContext';
import * as ROSLIB from 'roslib';
import { Info, ChevronDown, Power, Layers, Navigation, Map, Camera, Scan, Activity, FileText } from 'lucide-react';
import './MapPage.css';

// ── Shared helpers ──────────────────────────────────────────────────────────

const CollapsibleCategory = ({ title, subtitle, headerRight, children }) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div>
      <div className="accordion-header" onClick={() => setIsOpen(!isOpen)}>
        <div className="accordion-title-group">
          <h2 className="accordion-title">{title}</h2>
          <p className="accordion-subtitle">{subtitle}</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {headerRight && (
            <div onClick={(e) => e.stopPropagation()}>
              {headerRight}
            </div>
          )}
          <ChevronDown size={24} className={`accordion-icon ${isOpen ? 'open' : ''}`} />
        </div>
      </div>
      {isOpen && (
        <div className="accordion-content">
          {children}
        </div>
      )}
    </div>
  );
};

const BitConfig = ({ label, initialValue }) => {
  const [val, setVal] = useState(initialValue);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '4px' }}>
      <span style={{ fontSize: '0.8rem', color: '#a3a3a3' }}>{label}:</span>
      <input 
        type="text" 
        value={val} 
        onChange={e => setVal(e.target.value)}
        style={{ width: '40px', background: 'transparent', border: '1px solid #444', color: '#00f2fe', textAlign: 'center', borderRadius: '4px', fontSize: '0.8rem' }}
      />
    </div>
  );
};

// ── Toggle Row ───────────────────────────────────────────────────────────────
// Calls a std_srvs/srv/SetBool service with data=true (enable) or data=false (disable).

const ToggleRow = ({ title, serviceName, icon: Icon, desc, behavior, onHover }) => {
  const { ros, connectionStatus } = useRos();
  const [status, setStatus] = useState('');
  const [pending, setPending] = useState(false);

  const callSetBool = useCallback((enable) => {
    if (!ros || connectionStatus !== 'CONNECTED') {
      setStatus('Error: ROS not connected');
      return;
    }

    setPending(true);
    setStatus(enable ? 'Starting...' : 'Stopping...');

    const svc = new ROSLIB.Service({
      ros,
      name: serviceName,
      serviceType: 'std_srvs/srv/SetBool',
    });

    svc.callService(
      { data: enable },
      (res) => {
        setPending(false);
        setStatus(res.message || (enable ? 'Started' : 'Stopped'));
        setTimeout(() => setStatus(''), 4000);
      },
      (err) => {
        setPending(false);
        setStatus(`Error: ${err}`);
        setTimeout(() => setStatus(''), 5000);
      }
    );
  }, [ros, connectionStatus, serviceName]);

  return (
    <div
      className="service-row"
      onMouseEnter={() => onHover({ title, topic: serviceName, desc, behavior })}
    >
      <div className="row-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {Icon && <Icon size={18} style={{ color: '#00f2fe', flexShrink: 0 }} />}
          <h3 className="row-title">{title}</h3>
        </div>
        <span className="row-topic">{serviceName}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '16px', flexWrap: 'wrap' }}>
        {/* START button */}
        <button
          className="orange-btn"
          disabled={pending}
          onClick={() => callSetBool(true)}
        >
          START
        </button>

        {/* STOP button */}
        <button
          disabled={pending}
          onClick={() => callSetBool(false)}
          style={{
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.4)',
            borderRadius: '6px',
            padding: '8px 16px',
            color: '#f43f5e',
            fontWeight: 700,
            fontSize: '0.78rem',
            cursor: pending ? 'not-allowed' : 'pointer',
            opacity: pending ? 0.5 : 1,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.2s ease',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}
          onMouseEnter={(e) => { if (!pending) e.currentTarget.style.background = 'rgba(244, 63, 94, 0.3)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(244, 63, 94, 0.15)'; }}
        >
          STOP
        </button>

        {status && (
          <span style={{ fontSize: '0.8rem', color: '#f97316', fontStyle: 'italic' }}>
            {status}
          </span>
        )}
      </div>
    </div>
  );
};

// ── Page ─────────────────────────────────────────────────────────────────────

export default function PipelinePage() {
  const [activeInfo, setActiveInfo] = useState(null);

  return (
    <div className="map-page-wrapper">

      {/* LEFT: service list */}
      <div className="map-list-section">
        <div style={{ marginBottom: '20px' }}>
          <h1 style={{ margin: '0 0 4px 0', fontSize: '2rem', color: '#fff' }}>
            Pipeline Control
          </h1>
          <p style={{ margin: 0, color: '#a3a3a3' }}>
            Toggle <code style={{ color: '#f97316' }}>rover_autonomy</code> subsystems via
            the <code style={{ color: '#f97316' }}>main_compute</code> lifecycle node.
            Hover any row to see details.
          </p>
        </div>

        <CollapsibleCategory
          title="Navigation"
          subtitle="Nav2 stack — path planning, controller, and costmaps"
        >
          <ToggleRow
            title="Navigation"
            serviceName="/main_compute/set_navigation"
            icon={Navigation}
            desc="Starts or stops the full Nav2 navigation stack. When enabled, the rover can plan paths and autonomously drive to goal poses using BT Navigator, local/global planners, and costmaps."
            behavior="Enable when you want the rover to move autonomously. Disable to regain full manual control or to save resources during mapping-only sessions."
            onHover={setActiveInfo}
          />
        </CollapsibleCategory>

        <CollapsibleCategory
          title="Mapping"
          subtitle="SLAM / RTAB-Map — build and maintain the environment map"
          headerRight={<BitConfig label="Mode" initialValue="110" />}
        >
          <ToggleRow
            title="Mapping"
            serviceName="/main_compute/set_mapping"
            icon={Map}
            desc="Starts or stops the SLAM mapping subsystem (RTAB-Map). When enabled, the rover fuses RGB-D and LiDAR data to build and update the occupancy / 3-D map."
            behavior="Enable before beginning a new survey run. Disable to freeze the current map and save CPU when only navigating a known environment."
            onHover={setActiveInfo}
          />
          <ToggleRow
            title="Local Topography"
            serviceName="/main_compute/set_local_topography"
            icon={Layers}
            desc="Starts or stops the local terrain-elevation mapping subsystem (rover_topography). Generates a height-map around the rover using depth data."
            behavior="Enable when traversing uneven or outdoor terrain. Disable on flat indoor floors to reduce processing load."
            onHover={setActiveInfo}
          />
          <ToggleRow
            title="Global Topography"
            serviceName="/main_compute/set_global_topography"
            icon={Layers}
            desc="Starts or stops the global terrain-elevation mapping subsystem (rover_topography). Accumulates a large-scale height-map across the entire explored area."
            behavior="Enable for long-range outdoor missions. Disable when you only need a small local map or want to conserve memory."
            onHover={setActiveInfo}
          />
        </CollapsibleCategory>

        <CollapsibleCategory
          title="Localization"
          subtitle="Odometry sources and localization estimation"
          headerRight={<BitConfig label="Mode" initialValue="110" />}
        >
          <ToggleRow
            title="Odom from Camera 00"
            serviceName="/main_compute/set_odom_camera_00"
            icon={Activity}
            desc="Starts or stops visual odometry estimation from Camera 00."
            behavior="Enable for local pose estimation when Camera 00 is active."
            onHover={setActiveInfo}
          />
          <ToggleRow
            title="Odom from Camera 01"
            serviceName="/main_compute/set_odom_camera_01"
            icon={Activity}
            desc="Starts or stops visual odometry estimation from Camera 01."
            behavior="Enable for local pose estimation when Camera 01 is active."
            onHover={setActiveInfo}
          />
          <ToggleRow
            title="Odom from LiDAR 00"
            serviceName="/main_compute/set_odom_lidar_00"
            icon={Activity}
            desc="Starts or stops LiDAR odometry estimation from LiDAR 00."
            behavior="Enable for local pose estimation when LiDAR 00 is active."
            onHover={setActiveInfo}
          />
          <ToggleRow
            title="Localization"
            serviceName="/main_compute/set_localization"
            icon={Map}
            desc="Starts or stops the main localization fusion node (e.g., EKF or AMCL)."
            behavior="Enable to fuse odometry sources into a single reliable pose estimate."
            onHover={setActiveInfo}
          />
        </CollapsibleCategory>

        <CollapsibleCategory
          title="Sensors"
          subtitle="Hardware drivers — control data acquisition from sensors"
        >
          <ToggleRow
            title="Camera 00"
            serviceName="/main_compute/set_camera_00"
            icon={Camera}
            desc="Starts or stops the primary RGB-D camera driver node."
            behavior="Enable when you need visual feedback or point cloud data for mapping and obstacle avoidance."
            onHover={setActiveInfo}
          />
          <ToggleRow
            title="Camera 01 (Placeholder)"
            serviceName="/main_compute/set_camera_01"
            icon={Camera}
            desc="Placeholder for secondary RGB-D camera driver node."
            behavior="Currently a placeholder. Will be used for extended FOV."
            onHover={setActiveInfo}
          />
          <ToggleRow
            title="LiDAR 00"
            serviceName="/main_compute/set_lidar_00"
            icon={Scan}
            desc="Starts or stops the primary 2D/3D LiDAR driver node."
            behavior="Enable for mapping and precise obstacle detection."
            onHover={setActiveInfo}
          />
        </CollapsibleCategory>

        <CollapsibleCategory
          title="Description"
          subtitle="Robot physical model and transforms"
        >
          <ToggleRow
            title="Description"
            serviceName="/main_compute/set_description"
            icon={FileText}
            desc="Starts or stops the robot state publisher. When enabled, broadcasts the rover's TF tree and URDF model."
            behavior="Enable for visualizing the rover in RViz and for accurate sensor transforms. Rarely disabled during normal operation."
            onHover={setActiveInfo}
          />
        </CollapsibleCategory>
      </div>

      {/* RIGHT: sticky details panel */}
      <div className="map-info-section">
        {activeInfo ? (
          <div style={{ animation: 'fadeIn 0.3s ease' }}>
            <h2 className="info-title">{activeInfo.title}</h2>
            <div className="info-topic">{activeInfo.topic}</div>

            <p className="info-desc">{activeInfo.desc}</p>

            <div className="info-behavior">
              <strong>Behavior use:</strong><br /><br />
              {activeInfo.behavior}
            </div>

            <div style={{
              marginTop: '24px',
              padding: '14px 16px',
              background: 'rgba(0,242,254,0.05)',
              border: '1px solid rgba(0,242,254,0.15)',
              borderRadius: '8px',
              fontSize: '0.82rem',
              color: '#737373',
              lineHeight: 1.6,
            }}>
              <strong style={{ color: '#00f2fe' }}>Service type:</strong>
              <br />
              <code>std_srvs/srv/SetBool</code>
              <br /><br />
              <strong style={{ color: '#00f2fe' }}>Node:</strong>
              <br />
              <code>/main_compute</code> (lifecycle node)
            </div>
          </div>
        ) : (
          <div className="empty-info">
            <Info size={48} style={{ color: '#ea580c', marginBottom: '16px', opacity: 0.5 }} />
            <h3 style={{ color: '#fff' }}>Awaiting Selection</h3>
            <p>Hover over any pipeline module on the left to view its service details and operational use cases.</p>
          </div>
        )}
      </div>

    </div>
  );
}
