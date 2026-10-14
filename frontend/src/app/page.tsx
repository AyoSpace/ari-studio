"use client";

import React, { useState, useRef } from "react";
import { Sparkles, Mic, Image as ImageIcon, Layers, ChevronRight, SlidersHorizontal, Loader2, User, Shirt, X } from "lucide-react";

interface AcieData {
  concept_title: string;
  prompt_received: string;
  ai_reasoning: string;
  matched_vector_asset: string;
  image_url?: string;
  glb_model_url?: string;
  textile_node: string;
  color_palette: string[];
  jewelry_pairing: string;
  status: string;
}

export default function ARIStudio() {
  const [prompt, setPrompt] = useState("");
  const [viewMode, setViewMode] = useState<"2d" | "3d">("2d");
  const [displayMode, setDisplayMode] = useState<"ghost_mannequin" | "human_model">("ghost_mannequin");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [fabricFile, setFabricFile] = useState<File | null>(null);
  const [fabricPreview, setFabricPreview] = useState<string | null>(null);
  const [acieData, setAcieData] = useState<AcieData | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // 1. Browser Voice-to-Text Integration
  const handleVoiceInput = () => {
    if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setPrompt((prev) => (prev ? `${prev} ${transcript}` : transcript));
    };

    recognition.start();
  };

  // 2. Fabric Photo Attachment Handler
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFabricFile(file);
      setFabricPreview(URL.createObjectURL(file));
    }
  };

  // 3. Multi-Modal Synthesis Call
  const handleSynthesize = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("prompt", prompt);
    formData.append("display_mode", displayMode);
    if (fabricFile) {
      formData.append("fabric_image", fabricFile);
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/api/synthesize-multimodal", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }

      const data = await res.json();
      setAcieData(data);
    } catch (error) {
      console.error("Failed to fetch:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#07080B] text-[#F3F4F6] font-sans antialiased flex flex-col selection:bg-[#D4AF37]/20 selection:text-[#D4AF37]">
      {/* Header */}
      <header className="h-20 border-b border-[#161922] px-8 flex items-center justify-between bg-[#07080B]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <span className="font-serif text-2xl tracking-[0.2em] font-medium text-[#F3F4F6] uppercase">
            ARI Studio
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37]" />
          <span className="text-[10px] uppercase tracking-[0.25em] text-[#8C94A6] font-light">
            Creative Intelligence
          </span>
        </div>

        <nav className="hidden md:flex items-center space-x-8 text-[11px] uppercase tracking-[0.2em] text-[#8C94A6] font-medium">
          <a href="#" className="hover:text-[#F3F4F6] transition-colors">Studio</a>
          <a href="#" className="hover:text-[#F3F4F6] transition-colors">ACIE Engine</a>
          <a href="#" className="hover:text-[#F3F4F6] transition-colors">Knowledge Graph</a>
          <a href="#" className="hover:text-[#F3F4F6] transition-colors">Archive</a>
        </nav>

        <button className="text-[11px] uppercase tracking-[0.15em] px-6 py-2.5 rounded-full bg-[#0E1017] border border-[#1A1F2C] hover:border-[#D4AF37]/40 text-[#F3F4F6] transition-all">
          Workspace
        </button>
      </header>

      {/* Main Grid */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-8 p-8 max-w-[1700px] mx-auto w-full">
        {/* Control Panel */}
        <section className="lg:col-span-5 flex flex-col justify-between space-y-8">
          <div className="space-y-6">
            <div className="space-y-2">
              <span className="text-[10px] uppercase tracking-[0.3em] text-[#D4AF37] font-semibold">
                Global Rhythm • African Heartbeat
              </span>
              <h1 className="font-serif text-3xl md:text-4xl font-normal text-[#F3F4F6] leading-[1.15]">
                Synthesize High Fashion Concepts.
              </h1>
              <p className="text-xs text-[#8C94A6] font-light leading-relaxed">
                Express mood, voice directives, or fabric reference photos. ACIE traverses structural textiles, silhouettes, and material drapes automatically.
              </p>
            </div>

            {/* Presentation Mode Selector */}
            <div className="flex items-center space-x-2 bg-[#0E1017] p-1.5 rounded-xl border border-[#1A1F2C] w-fit">
              <button
                onClick={() => setDisplayMode("ghost_mannequin")}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-[10px] uppercase tracking-wider transition-all ${
                  displayMode === "ghost_mannequin" ? "bg-[#1A1F2C] text-[#D4AF37] font-medium" : "text-[#8C94A6]"
                }`}
              >
                <Shirt className="w-3.5 h-3.5" />
                <span>Floating Concept</span>
              </button>
              <button
                onClick={() => setDisplayMode("human_model")}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-[10px] uppercase tracking-wider transition-all ${
                  displayMode === "human_model" ? "bg-[#1A1F2C] text-[#D4AF37] font-medium" : "text-[#8C94A6]"
                }`}
              >
                <User className="w-3.5 h-3.5" />
                <span>On Model (Optional)</span>
              </button>
            </div>

            {/* Prompt Input Box */}
            <div className="relative rounded-2xl bg-[#0E1017] border border-[#1A1F2C] p-5 focus-within:border-[#D4AF37]/50 transition-all shadow-xl space-y-3">
              <textarea
  rows={3}
  value={prompt}
  onChange={(e) => setPrompt(e.target.value)}
  placeholder="ARI, create a black leather baggy trouser with grey leather patch in the ankle lengths..."
  className="w-full bg-transparent text-sm text-[#F3F4F6] placeholder-[#8C94A6]/40 focus:outline-none resize-none font-light leading-relaxed"
  suppressHydrationWarning
  spellCheck={false}
/>

              {/* Fabric Attachment Thumbnail */}
              {fabricPreview && (
                <div className="flex items-center space-x-3 bg-[#07080B] p-2 rounded-xl border border-[#1A1F2C] w-fit">
                  <img src={fabricPreview} alt="Fabric texture reference" className="w-10 h-10 object-cover rounded-lg" />
                  <span className="text-[10px] text-[#D4AF37]">Fabric Texture Attached</span>
                  <button
                    onClick={() => {
                      setFabricFile(null);
                      setFabricPreview(null);
                    }}
                    className="p-1 hover:text-red-400 text-[#8C94A6]"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              <div className="flex items-center justify-between pt-3 border-t border-[#161922]">
                <div className="flex items-center space-x-2 text-[#8C94A6]">
                  <button
                    onClick={handleVoiceInput}
                    className={`p-2 hover:bg-[#161922] rounded-lg transition-colors ${
                      isListening ? "text-[#D4AF37] animate-pulse" : "hover:text-[#F3F4F6]"
                    }`}
                    title="Voice Input Directive"
                  >
                    <Mic className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 hover:bg-[#161922] hover:text-[#F3F4F6] rounded-lg transition-colors"
                    title="Upload Fabric Reference Image"
                  >
                    <ImageIcon className="w-4 h-4" />
                  </button>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept="image/*"
                    className="hidden"
                  />

                  <button className="p-2 hover:bg-[#161922] hover:text-[#F3F4F6] rounded-lg transition-colors" title="Style Controls">
                    <SlidersHorizontal className="w-4 h-4" />
                  </button>
                </div>

                <button
                  onClick={handleSynthesize}
                  disabled={loading}
                  className="flex items-center space-x-2 bg-[#F3F4F6] hover:bg-[#D4AF37] text-[#07080B] font-medium px-5 py-2.5 rounded-xl text-xs tracking-wider transition-all shadow-lg disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <span>Synthesizing</span>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    </>
                  ) : (
                    <>
                      <span>Generate Look</span>
                      <Sparkles className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Culture Tags */}
            <div className="space-y-3">
              <span className="text-[10px] uppercase tracking-[0.2em] text-[#8C94A6]">Selected Tones</span>
              <div className="flex flex-wrap gap-2">
                {["Lagos Streetwear", "Ottoman Luxe", "Sculptural Silhouettes", "Brushed Brass"].map((tag) => (
                  <button
                    key={tag}
                    onClick={() => setPrompt((prev) => (prev ? `${prev}, ${tag}` : tag))}
                    className="px-4 py-1.5 rounded-full text-[11px] bg-[#0E1017] border border-[#1A1F2C] text-[#8C94A6] hover:text-[#F3F4F6] transition-all"
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* ACIE Card */}
          <div className="p-5 rounded-2xl bg-[#0E1017]/80 border border-[#1A1F2C] space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-[#D4AF37]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#D4AF37] animate-pulse" />
                <span className="text-[10px] uppercase tracking-[0.2em] font-semibold">ACIE Knowledge Graph</span>
              </div>
              <span className="text-[10px] text-[#8C94A6]">FastAPI Live</span>
            </div>
            <p className="text-xs text-[#8C94A6] font-light leading-relaxed">
              <strong className="text-[#F3F4F6] font-normal">Textile Node:</strong>{" "}
              {acieData ? acieData.textile_node : "Heavy Aso-Oke Weave paired with Silk Satin."} <br />
              <strong className="text-[#F3F4F6] font-normal">Jewelry Match:</strong>{" "}
              {acieData ? acieData.jewelry_pairing : "Layered Coral Brass Cuffs."}
            </p>
          </div>
        </section>

        {/* Studio Canvas Viewport */}
        <section className="lg:col-span-7 bg-[#0E1017] border border-[#1A1F2C] rounded-3xl p-8 flex flex-col justify-between relative overflow-hidden min-h-[550px] shadow-2xl">
          <div className="flex items-center justify-between z-10">
            <span className="text-[10px] uppercase tracking-[0.25em] text-[#8C94A6]">Studio Viewport</span>
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1 bg-[#07080B] p-1 rounded-xl border border-[#161922]">
                <button
                  onClick={() => setViewMode("2d")}
                  className={`px-3.5 py-1.5 rounded-lg text-[10px] uppercase tracking-wider transition-all ${
                    viewMode === "2d" ? "bg-[#1A1F2C] text-[#F3F4F6] font-medium" : "text-[#8C94A6] hover:text-[#F3F4F6]"
                  }`}
                >
                  Visual Mode
                </button>
                <button
                  onClick={() => setViewMode("3d")}
                  className={`px-3.5 py-1.5 rounded-lg text-[10px] uppercase tracking-wider transition-all ${
                    viewMode === "3d" ? "bg-[#1A1F2C] text-[#D4AF37] font-medium" : "text-[#8C94A6] hover:text-[#F3F4F6]"
                  }`}
                >
                  3D Render Mode
                </button>
              </div>
            </div>
          </div>

          {/* Viewport Render Display */}
          <div className="my-auto flex flex-col items-center justify-center text-center p-6 z-10 space-y-4 w-full">
            {viewMode === "3d" ? (
              <div className="w-full max-w-md h-80 rounded-2xl overflow-hidden border border-[#1A1F2C] bg-[#07080B] relative shadow-2xl flex flex-col items-center justify-center">
                {acieData?.glb_model_url ? (
                  <iframe
                    src={acieData.glb_model_url}
                    className="w-full h-full border-0"
                    title="Tripo3D Garment Mesh"
                  />
                ) : (
                  <div className="relative flex items-center justify-center w-48 h-56">
                    <div className="absolute inset-0 flex items-center justify-center animate-[spin_12s_linear_infinite]">
                      <div className="w-40 h-40 rounded-full border border-[#D4AF37]/30 border-dashed" />
                    </div>
                    <svg className="w-32 h-48 drop-shadow-[0_10px_20px_rgba(212,175,55,0.15)]" viewBox="0 0 100 150" fill="none">
                      <rect x="30" y="20" width="40" height="10" rx="3" fill="#1A1714" stroke="#D4AF37" strokeWidth="1.5" />
                      <path d="M32 30 L22 120 L44 120 L48 30 Z" fill="#0E1017" stroke="#1A1F2C" strokeWidth="1.5" />
                      <path d="M52 30 L56 120 L78 120 L68 30 Z" fill="#0E1017" stroke="#1A1F2C" strokeWidth="1.5" />
                      <rect x="23" y="100" width="20" height="16" rx="2" fill="#4A4E69" stroke="#D4AF37" strokeWidth="1" />
                      <rect x="57" y="100" width="20" height="16" rx="2" fill="#4A4E69" stroke="#D4AF37" strokeWidth="1" />
                    </svg>
                  </div>
                )}
                <div className="absolute bottom-3 left-3 text-[9px] uppercase tracking-widest text-[#D4AF37] bg-[#0E1017]/90 px-3 py-1 rounded-full border border-[#D4AF37]/30 backdrop-blur-md">
                  Parametric Garment 3D Viewport
                </div>
              </div>
            ) : acieData?.image_url ? (
              <div className="w-full max-w-md h-80 rounded-2xl overflow-hidden border border-[#1A1F2C] relative group shadow-2xl">
                <img
                  src={acieData.image_url}
                  alt={acieData.concept_title}
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />
              </div>
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-[#07080B] border border-[#1A1F2C] flex items-center justify-center text-[#D4AF37]">
                <Layers className="w-7 h-7 stroke-[1.25]" />
              </div>
            )}

            <div className="space-y-2 max-w-lg">
              <p className="font-serif text-2xl text-[#F3F4F6] font-normal">
                {acieData ? acieData.concept_title : "Awaiting Render Directive"}
              </p>
              <p className="text-xs text-[#8C94A6] font-light leading-relaxed mx-auto">
                {acieData
                  ? acieData.ai_reasoning
                  : "Multi-angle high resolution views, material textures, and color swatch cards will render here."}
              </p>
              {acieData && (
                <div className="pt-2">
                  <span className="text-[10px] uppercase tracking-[0.2em] px-3.5 py-1.5 rounded-full bg-[#1A1F2C] text-[#D4AF37] border border-[#D4AF37]/30">
                    {acieData.matched_vector_asset}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Footer Swatches */}
          <div className="flex items-center justify-between pt-6 border-t border-[#161922] z-10">
            <div className="flex items-center space-x-4">
              <span className="text-[10px] uppercase tracking-[0.2em] text-[#8C94A6]">Palette</span>
              <div className="flex space-x-2">
                {(acieData?.color_palette || ["#0D1626", "#D4AF37", "#7A2E22", "#E2D1B8"]).map((color, index) => (
                  <div
                    key={index}
                    className="w-5 h-5 rounded-full border border-[#1A1F2C]"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
            </div>
            <button className="flex items-center space-x-2 text-xs text-[#F3F4F6] hover:text-[#D4AF37] transition-colors">
              <span className="uppercase tracking-widest text-[11px]">Export Lookbook</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
