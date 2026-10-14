"use client";

import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Float } from "@react-three/drei";
import * as THREE from "three";

function GarmentMannequin3D() {
  const groupRef = useRef<THREE.Group>(null!);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.5;
    }
  });

  return (
    <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
      <group ref={groupRef} position={[0, -0.8, 0]}>
        {/* Torso / Waist */}
        <mesh position={[0, 1.4, 0]}>
          <cylinderGeometry args={[0.35, 0.28, 0.8, 32]} />
          <meshStandardMaterial color="#1A1F2C" roughness={0.4} metalness={0.6} />
        </mesh>
        {/* Left Leg / Pant Structure */}
        <mesh position={[-0.18, 0.5, 0]} rotation={[0, 0, -0.05]}>
          <cylinderGeometry args={[0.16, 0.22, 1.1, 32]} />
          <meshStandardMaterial color="#0E1017" roughness={0.3} metalness={0.8} />
        </mesh>
        {/* Right Leg / Pant Structure */}
        <mesh position={[0.18, 0.5, 0]} rotation={[0, 0, 0.05]}>
          <cylinderGeometry args={[0.16, 0.22, 1.1, 32]} />
          <meshStandardMaterial color="#0E1017" roughness={0.3} metalness={0.8} />
        </mesh>
        {/* Ankle Patches (Gold Accent) */}
        <mesh position={[-0.18, 0.05, 0]}>
          <cylinderGeometry args={[0.225, 0.21, 0.25, 32]} />
          <meshStandardMaterial color="#D4AF37" roughness={0.2} metalness={0.9} />
        </mesh>
        <mesh position={[0.18, 0.05, 0]}>
          <cylinderGeometry args={[0.225, 0.21, 0.25, 32]} />
          <meshStandardMaterial color="#D4AF37" roughness={0.2} metalness={0.9} />
        </mesh>
      </group>
    </Float>
  );
}

export default function Studio3DCanvas() {
  return (
    <div className="w-full max-w-md h-80 rounded-2xl overflow-hidden border border-[#1A1F2C] bg-[#07080B] relative shadow-2xl">
      <Canvas camera={{ position: [0, 0, 3.5], fov: 45 }}>
        <ambientLight intensity={0.8} />
        <directionalLight position={[5, 10, 7]} intensity={1.8} color="#F3F4F6" />
        <pointLight position={[-5, -5, -5]} intensity={1.0} color="#D4AF37" />
        <GarmentMannequin3D />
        <OrbitControls enableZoom={true} autoRotate={false} />
      </Canvas>
      <div className="absolute bottom-3 left-3 text-[9px] uppercase tracking-widest text-[#D4AF37] bg-[#0E1017]/90 px-3 py-1 rounded-full border border-[#D4AF37]/30 backdrop-blur-md">
        Parametric Garment 3D Viewport
      </div>
    </div>
  );
}

