"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Line, MeshDistortMaterial, OrbitControls, Sparkles } from "@react-three/drei";
import { useRef } from "react";
import * as THREE from "three";

function Core() {
  const shell = useRef<THREE.Group>(null);
  const ringA = useRef<THREE.Mesh>(null);
  const ringB = useRef<THREE.Mesh>(null);
  const ringC = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    const d = Math.min(delta, 0.033);
    if (shell.current) {
      shell.current.rotation.y += d * 0.085;
      shell.current.rotation.x = Math.sin(state.clock.elapsedTime * .28) * .055;
    }
    if (ringA.current) ringA.current.rotation.z += d * .12;
    if (ringB.current) ringB.current.rotation.z -= d * .075;
    if (ringC.current) ringC.current.rotation.y += d * .06;
  });

  return (
    <group ref={shell}>
      <Float speed={1.05} rotationIntensity={0.16} floatIntensity={0.22}>
        <mesh>
          <icosahedronGeometry args={[0.96, 5]} />
          <MeshDistortMaterial color="#4f6fdf" roughness={0.28} metalness={0.04} distort={0.12} speed={0.58} />
        </mesh>
        <mesh scale={1.16}>
          <icosahedronGeometry args={[0.96, 2]} />
          <meshBasicMaterial color="#9fb3ec" wireframe transparent opacity={0.28} />
        </mesh>
        <mesh scale={0.72}>
          <icosahedronGeometry args={[0.96, 2]} />
          <meshBasicMaterial color="#dce6ff" wireframe transparent opacity={0.16} />
        </mesh>
      </Float>
      <mesh ref={ringA} rotation={[Math.PI / 2.3, 0, 0]}>
        <torusGeometry args={[1.68, .0065, 8, 128]} />
        <meshBasicMaterial color="#3157d5" transparent opacity={0.48} />
      </mesh>
      <mesh ref={ringB} rotation={[Math.PI / 2.05, .6, .2]}>
        <torusGeometry args={[2.18, .0055, 8, 128]} />
        <meshBasicMaterial color="#2a91a8" transparent opacity={0.24} />
      </mesh>
      <mesh ref={ringC} rotation={[.5, .25, Math.PI / 2]}>
        <torusGeometry args={[2.56, .004, 8, 128]} />
        <meshBasicMaterial color="#f0ae5a" transparent opacity={0.16} />
      </mesh>
      <Line points={[[-2.75, 0, 0], [-1.25, 0, 0]]} color="#7e93c7" lineWidth={.6} transparent opacity={.5} />
      <Line points={[[1.25, 0, 0], [2.75, 0, 0]]} color="#7e93c7" lineWidth={.6} transparent opacity={.5} />
      <Sparkles count={24} scale={5.8} size={0.85} speed={0.1} opacity={0.20} color="#5575df" />
    </group>
  );
}

export function HeroCoreCanvas() {
  return (
    <Canvas
      camera={{ position: [0, 0.08, 7.8], fov: 38 }}
      dpr={[1, 1.25]}
      performance={{ min: 0.65 }}
      gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
    >
      <ambientLight intensity={1.35} />
      <directionalLight position={[4, 4, 5]} intensity={2.1} color="#ffffff" />
      <pointLight position={[-4, -1, 2]} intensity={1.5} color="#6c85ea" />
      <pointLight position={[3, -2, 1]} intensity={.9} color="#74c2cf" />
      <Core />
      <OrbitControls enableZoom={false} enablePan={false} rotateSpeed={0.25} autoRotate autoRotateSpeed={0.12} dampingFactor={0.08} enableDamping />
    </Canvas>
  );
}
