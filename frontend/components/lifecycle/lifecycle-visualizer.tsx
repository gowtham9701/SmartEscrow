'use client';

import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Html, OrbitControls } from '@react-three/drei';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { Group, Mesh } from 'three';

export const LIFECYCLE_STAGES = [
  {
    key: 'vetting',
    label: 'Vetting',
    blurb: 'AI screens the contributor’s skills and ranks the match.',
  },
  {
    key: 'locked',
    label: 'Milestone Locked',
    blurb: 'Scope and milestone are agreed and locked by both parties.',
  },
  {
    key: 'escrowed',
    label: 'Funds Escrowed',
    blurb: 'Client USD is blocked in escrow — guaranteed, not yet paid.',
  },
  {
    key: 'release',
    label: 'Release',
    blurb: 'Verified delivery auto-releases the payout to the contributor.',
  },
] as const;

const ACCENT = '#c8502d';
const NAVY = '#1d2a44';
const PAPER = '#f4f2ee';
const GOLD = '#e0a24e';

const NODE_X = [-4.5, -1.5, 1.5, 4.5];

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

/** A single stage orb. Glows accent once reached, pulses while active. */
function StageNode({
  x,
  reached,
  active,
}: {
  x: number;
  reached: boolean;
  active: boolean;
}) {
  const ref = useRef<Mesh>(null);
  useFrame((state) => {
    if (!ref.current) return;
    const pulse = active ? 1 + Math.sin(state.clock.elapsedTime * 3) * 0.08 : 1;
    ref.current.scale.setScalar(lerp(ref.current.scale.x, pulse, 0.2));
  });
  return (
    <group position={[x, 0, 0]}>
      <mesh ref={ref}>
        <icosahedronGeometry args={[0.62, 1]} />
        <meshStandardMaterial
          color={reached ? ACCENT : NAVY}
          emissive={reached ? ACCENT : NAVY}
          emissiveIntensity={active ? 0.9 : reached ? 0.45 : 0.12}
          metalness={0.4}
          roughness={0.25}
          flatShading
        />
      </mesh>
      {/* Halo ring on the active node */}
      {active && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.95, 0.03, 12, 48]} />
          <meshBasicMaterial color={GOLD} />
        </mesh>
      )}
    </group>
  );
}

/** The connective pipe between two nodes; fills with accent as progress passes. */
function Pipe({ x, filled }: { x: number; filled: boolean }) {
  return (
    <mesh position={[x, 0, 0]}>
      <boxGeometry args={[3, 0.07, 0.07]} />
      <meshStandardMaterial
        color={filled ? ACCENT : NAVY}
        emissive={filled ? ACCENT : '#000000'}
        emissiveIntensity={filled ? 0.5 : 0}
        transparent
        opacity={filled ? 1 : 0.4}
      />
    </mesh>
  );
}

/** The escrow cube that travels the pipeline toward the active stage. */
function EscrowCube({ targetX }: { targetX: number }) {
  const ref = useRef<Mesh>(null);
  useFrame(() => {
    if (!ref.current) return;
    ref.current.position.x = lerp(ref.current.position.x, targetX, 0.06);
    ref.current.rotation.x += 0.01;
    ref.current.rotation.y += 0.015;
  });
  return (
    <Float speed={2} floatIntensity={0.4} rotationIntensity={0}>
      <mesh ref={ref} position={[NODE_X[0], 1.4, 0]}>
        <boxGeometry args={[0.5, 0.5, 0.5]} />
        <meshStandardMaterial
          color={GOLD}
          emissive={GOLD}
          emissiveIntensity={0.6}
          metalness={0.7}
          roughness={0.2}
        />
      </mesh>
    </Float>
  );
}

function Scene({ stage }: { stage: number }) {
  const group = useRef<Group>(null);
  useFrame((state) => {
    if (!group.current) return;
    // Gentle parallax sway rather than a full spin (keeps labels legible).
    group.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.25) * 0.18;
  });

  const nodes = useMemo(
    () =>
      NODE_X.map((x, i) => ({
        x,
        reached: i <= stage,
        active: i === stage,
        label: LIFECYCLE_STAGES[i].label,
      })),
    [stage],
  );

  return (
    <group ref={group}>
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 6, 5]} intensity={1.1} />
      <pointLight position={[0, 2, 4]} intensity={40} color={ACCENT} />

      {NODE_X.slice(0, -1).map((x, i) => (
        <Pipe key={i} x={(NODE_X[i] + NODE_X[i + 1]) / 2} filled={i < stage} />
      ))}

      {nodes.map((n, i) => (
        <group key={i}>
          <StageNode x={n.x} reached={n.reached} active={n.active} />
          <Html position={[n.x, -1.25, 0]} center distanceFactor={10}>
            <div
              style={{
                fontFamily: 'var(--font-mono, ui-monospace)',
                fontSize: 11,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                whiteSpace: 'nowrap',
                color: n.active ? ACCENT : n.reached ? PAPER : 'rgba(244,242,238,0.5)',
                fontWeight: n.active ? 700 : 500,
              }}
            >
              {`0${i + 1} ${n.label}`}
            </div>
          </Html>
        </group>
      ))}

      <EscrowCube targetX={NODE_X[Math.min(stage, NODE_X.length - 1)]} />

      <OrbitControls
        enablePan={false}
        enableZoom={false}
        minPolarAngle={Math.PI / 2.6}
        maxPolarAngle={Math.PI / 1.9}
      />
    </group>
  );
}

/**
 * 3D contract-lifecycle visualizer.
 * Vetting -> Milestone Locked -> Funds Escrowed -> Release, with WebGL transitions.
 * `activeStage` (0-3) can be driven externally; otherwise it auto-advances.
 */
export function LifecycleVisualizer({
  activeStage,
  autoPlay = true,
  height = 420,
}: {
  activeStage?: number;
  autoPlay?: boolean;
  height?: number;
}) {
  const [internal, setInternal] = useState(0);
  const controlled = typeof activeStage === 'number';
  const stage = controlled ? Math.max(0, Math.min(3, activeStage!)) : internal;

  // Auto-advance when uncontrolled.
  useEffect(() => {
    if (controlled || !autoPlay) return;
    const id = setInterval(() => {
      setInternal((s) => (s + 1) % LIFECYCLE_STAGES.length);
    }, 2600);
    return () => clearInterval(id);
  }, [controlled, autoPlay]);

  return (
    <div className="w-full">
      <div
        className="overflow-hidden rounded-2xl border border-ink/10"
        style={{ height, background: 'radial-gradient(120% 120% at 50% 0%, #121a2e 0%, #0d1117 70%)' }}
      >
        <Canvas camera={{ position: [0, 1.5, 9], fov: 45 }} dpr={[1, 2]}>
          <Scene stage={stage} />
        </Canvas>
      </div>

      {!controlled && (
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
          {LIFECYCLE_STAGES.map((s, i) => (
            <button
              key={s.key}
              onClick={() => setInternal(i)}
              className={`rounded-full px-4 py-2 font-mono text-[11px] uppercase tracking-wide transition ${
                i === stage
                  ? 'bg-accent text-paper'
                  : 'border border-ink/20 text-ink/70 hover:border-ink hover:text-ink'
              }`}
            >
              {`0${i + 1} · ${s.label}`}
            </button>
          ))}
        </div>
      )}

      <p className="mt-3 text-center font-mono text-sm text-ink/70">
        {LIFECYCLE_STAGES[stage].blurb}
      </p>
    </div>
  );
}

export default LifecycleVisualizer;
