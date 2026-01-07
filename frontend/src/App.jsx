import React, { useEffect, useRef, useState } from "react";

// -------- API base (use proxy / same-origin when possible) --------
// priority: window.__API_BASE__ -> env -> ""
// when "" it will call /api/* which Vite can proxy to backend
// eslint-disable-next-line no-undef
const ENV_API = typeof process !== "undefined" && process?.env?.VITE_API_BASE ? process.env.VITE_API_BASE : "";
const API_BASE = (typeof window !== "undefined" ? (window.__API_BASE__ || "") : "") || ENV_API;

// -------- helpers --------
const srOnly = { position: "absolute", width: 1, height: 1, padding: 0, margin: -1, overflow: "hidden", clip: "rect(0,0,0,0)", whiteSpace: "nowrap", border: 0 };

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

function useLocalStorage(key, init) {
  const [v, setV] = useState(() => {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : init;
    } catch {
      return init;
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(v));
    } catch {}
  }, [key, v]);
  return [v, setV];
}

function useVoices(lang) {
  const [voices, setVoices] = useState([]);
  useEffect(() => {
    const load = () => {
      const v = (window.speechSynthesis?.getVoices?.() || []);
      if (v.length) setVoices(v);
    };
    load();
    // iOS: voices 可能延迟才到
    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = load;
      // 再保险：延时再探一次
      setTimeout(load, 500);
      setTimeout(load, 1500);
    }
    return () => {
      if (window.speechSynthesis) window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);
  const preferred =
    voices.find(v => (lang === 'zh' ? v.lang?.startsWith('zh') : v.lang?.startsWith('en'))) ||
    voices[0];
  return preferred;
}

function useTTSSafe(lang, enabled = true) {
  const voice = useVoices(lang);
  const unlockedRef = useRef(false);

  // 供"解锁"音频使用：在首次用户手势里调用
  const unlock = () => {
    try {
      if (!('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(' ');
      u.volume = 0;               // 静音"预热"
      u.rate = 1;
      u.pitch = 1;
      u.lang = lang === 'zh' ? 'zh-CN' : 'en-US';
      if (voice) u.voice = voice;
      window.speechSynthesis.speak(u);
      unlockedRef.current = true;
    } catch {}
  };

  // 说话：默认加入一个小延时（iOS 从录音切回播报需要时间）
  const speak = async (text, { delay = 0 } = {}) => {
    try {
      if (!enabled || !text || !('speechSynthesis' in window)) return;
      if (!unlockedRef.current) unlock();
      if (delay) await wait(delay);
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang === 'zh' ? 'zh-CN' : 'en-US';
      if (voice) u.voice = voice;
      u.volume = 1;
      u.rate = 1.0;
      u.pitch = 1.0;
      window.speechSynthesis.speak(u);
    } catch (e) {
      console.warn('TTS speak failed:', e);
    }
  };

  return { speak, unlock };
}

// API calls
async function apiStart(body){
  const r = await fetch(`${API_BASE}/api/start`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) });
  if(!r.ok) throw new Error(`start ${r.status}`); return r.json();
}

export default function App(){
  // developer controls (top small bar)
  const [lang, setLang] = useLocalStorage("lang","en");
  const [sessionId, setSessionId] = useLocalStorage("session_id","T"+Math.floor(Math.random()*1000));
  
  // 当sessionId变化时，清除位置询问计数
  useEffect(() => {
    const clearLocationInquiryCount = () => {
      const oldSessionId = sessionId;
      if (oldSessionId) {
        localStorage.removeItem(`location_inquiry_${oldSessionId}`);
        console.log(`🔄 Cleared location inquiry count for session: ${oldSessionId}`);
      }
    };
    
    // 在组件卸载时清除
    return clearLocationInquiryCount;
  }, [sessionId]);
  const [provider, setProvider] = useLocalStorage("provider","ft");
  const [siteId, setSiteId] = useLocalStorage("site_id","SCENE_A_MS");
  
  // Development controls for ground truth
  // const [devGTNodeId, setDevGTNodeId] = useLocalStorage("dev_gt_node_id", ""); // REMOVED
  const [showDevInfo, setShowDevInfo] = useState(false);

  // ✅ 新增：RQ3 状态管理
  const [currentClarificationId, setCurrentClarificationId] = useState(null);
  const [clarificationRoundCount, setClarificationRoundCount] = useState(0);
  const [currentRecoveryId, setCurrentRecoveryId] = useState(null);
  const [lastPredictedNode, setLastPredictedNode] = useState("");
  const [lastGtNode, setLastGtNode] = useState("");

  // modes & ui
  const [started, setStarted] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState("");

  // dialog messages
  const [messages, setMessages] = useState([]); // {role:"system"|"you"|"assistant", text}

  // TTS
  const [ttsEnabled] = useState(true);
  const { speak, unlock } = useTTSSafe(lang, ttsEnabled);

  // recording
  const mediaRecorderRef = useRef(null); const chunksRef = useRef([]); const timerRef = useRef(null);
  const [recording, setRecording] = useState(false); const [duration, setDuration] = useState(0);

  // photo
  const fileInputRef = useRef(null);

  // API calls - moved inside component to access state variables
  const apiLocate = async (site_id, fileOrBlob, nameHint="photo.jpg", firstPhoto = false) => {
    const reqId = crypto.randomUUID(); // Generate unique request ID
    const clientStartMs = Date.now(); // Record client start time
    
    const fd = new FormData();
    let blob = fileOrBlob;
    if (fileOrBlob instanceof File) {
      blob = await compressImage(fileOrBlob);
      nameHint = fileOrBlob.name.replace(/\.[^.]+$/, ".jpg");
    }
    fd.append("site_id", site_id);
    fd.append("image", new File([blob], nameHint, { type: "image/jpeg" }));
    
    // Add development controls
    fd.append("session_id", sessionId);
    fd.append("provider", provider);
    
    // ✅ GT Node ID will be manually recorded by experimenter
    // if (devGTNodeId) fd.append("gt_node_id", devGTNodeId);
    
    // ✅ 端到端起点 + 请求 id
    fd.append("client_start_ms", String(clientStartMs));
    fd.append("req_id", reqId);
    fd.append("first_photo", firstPhoto.toString());
    
    console.log("📤 API call params:", { site_id, firstPhoto, sessionId, provider });
    console.log("📤 FormData first_photo value:", fd.get("first_photo"));
    
    const r = await fetch(`${API_BASE}/api/locate`, { method:"POST", body:fd });
    if(!r.ok) throw new Error(`locate ${r.status}`); 
    
    const resp = await r.json();
    
    // 播报前的时刻（用于 e2e）
    const ttsStartMs = Date.now();
    
    // 告知后端记录端到端时延
    fetch(`${API_BASE}/api/metrics/tts_start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        req_id: resp.req_id || reqId,
        session_id: sessionId,
        site_id: siteId,
        provider: provider,  // ✅ 新增 provider 字段
        client_start_ms: clientStartMs,
        client_tts_start_ms: ttsStartMs
      })
    }).catch(() => {}); // Ignore errors for metrics
    
    return resp;
  };

  const apiQA = async (body) => {
    const r = await fetch(`${API_BASE}/api/qa`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) });
    if(!r.ok) throw new Error(`qa ${r.status}`); 
    return r.json();
  };

  // ✅ New: Location tracking API calls
  const getSessionLocation = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/session/location/${sessionId}`);
      if (!r.ok) throw new Error(`location ${r.status}`);
      const data = await r.json();
      
      setCurrentLocation(data.current_location);
      setLocationHistory(data.location_history || []);
      setLocationConfidence(data.confidence_history?.[data.confidence_history.length - 1] || 0);
      
      console.log("📍 Location updated:", data.current_location, "confidence:", data.confidence_history?.[data.confidence_history.length - 1]);
      return data;
    } catch (e) {
      console.warn("Failed to get session location:", e);
      return null;
    }
  };

  const getSessionStatus = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/session/status/${sessionId}`);
      if (!r.ok) throw new Error(`status ${r.status}`);
      return await r.json();
    } catch (e) {
      console.warn("Failed to get session status:", e);
      return null;
    }
  };

  // ✅ New: Location verification and navigation functions
  const verifyLocation = async (destination = null) => {
    try {
      const url = destination 
        ? `${API_BASE}/api/location/verify/${sessionId}?destination=${encodeURIComponent(destination)}`
        : `${API_BASE}/api/location/verify/${sessionId}`;
      
      const r = await fetch(url);
      if (!r.ok) throw new Error(`verify ${r.status}`);
      const data = await r.json();
      
      console.log("📍 Location verification result:", data);
      return data;
    } catch (e) {
      console.warn("Failed to verify location:", e);
      return null;
    }
  };

  const getNavigationInstructions = async (destination) => {
    try {
      const r = await fetch(`${API_BASE}/api/location/navigate/${sessionId}?destination=${encodeURIComponent(destination)}`);
      if (!r.ok) throw new Error(`navigate ${r.status}`);
      const data = await r.json();
      
      console.log("🧭 Navigation instructions:", data);
      return data;
    } catch (e) {
      console.warn("Failed to get navigation instructions:", e);
      return null;
    }
  };

  // ✅ 新增：RQ3 澄清对话记录
  const recordClarificationRound = async (userQuestion, systemAnswer, predictedNode) => {
    if (!currentClarificationId) return;
    
    const roundData = {
      clarification_id: currentClarificationId,
      session_id: sessionId,
      site_id: siteId,
      provider: provider,  // ✅ 新增 provider 字段
      round_count: clarificationRoundCount + 1,
      user_question: userQuestion,
      system_answer: systemAnswer,
      predicted_node: predictedNode,
      gt_node_id: "" // Will be manually recorded by experimenter
    };
    
    try {
      await fetch(`${API_BASE}/api/metrics/clarification_round`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(roundData)
      });
      setClarificationRoundCount(prev => prev + 1);
    } catch (e) {
      console.warn("Failed to record clarification round:", e);
    }
  };

  const endClarificationSession = async (finalPredictedNode) => {
    if (!currentClarificationId) return;
    
    const endData = {
      clarification_id: currentClarificationId,
      session_id: sessionId,
      site_id: siteId,
      provider: provider,  // ✅ 新增 provider 字段
      total_rounds: clarificationRoundCount,
      final_predicted_node: finalPredictedNode,
      gt_node_id: "" // Will be manually recorded by experimenter
    };
    
    try {
      await fetch(`${API_BASE}/api/metrics/clarification_end`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(endData)
      });
      
      // 重置澄清会话状态
      setCurrentClarificationId(null);
      setClarificationRoundCount(0);
    } catch (e) {
      console.warn("Failed to end clarification session:", e);
    }
  };

  // ✅ New: RQ3 error recovery recording
  const startErrorRecovery = async (errorNode, correctNode) => {
    const recoveryData = {
      session_id: sessionId,
      site_id: siteId,
      provider: provider,  // ✅ New: provider field
      error_node: errorNode,
      correct_node: correctNode || "unknown" // GT will be manually recorded
    };
    
    try {
      const response = await fetch(`${API_BASE}/api/metrics/error_recovery_start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(recoveryData)
      });
      const result = await response.json();
      setCurrentRecoveryId(result.recovery_id);
      console.log("Error recovery started:", result.recovery_id);
    } catch (e) {
      console.warn("Failed to start error recovery:", e);
    }
  };

  const endErrorRecovery = async (correctNode, recoveryPath = "") => {
    if (!currentRecoveryId) return;
    
    const recoveryData = {
      recovery_id: currentRecoveryId,
      session_id: sessionId,
      site_id: siteId,
      provider: provider,  // ✅ New: provider field
      correct_node: correctNode,
      recovery_path: recoveryPath
    };
    
    try {
      const response = await fetch(`${API_BASE}/api/metrics/error_recovery_end`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(recoveryData)
      });
      const result = await response.json();
      console.log("Error recovery completed:", result.recovery_duration_ms, "ms");
      
      // 重置错误恢复状态
      setCurrentRecoveryId(null);
    } catch (e) {
      console.warn("Failed to end error recovery:", e);
    }
  };

  // ✅ New: Logging control functions
  const [loggingEnabled, setLoggingEnabled] = useState(false);
  const [currentRunId, setCurrentRunId] = useState("");
  
  // ✅ New: First photo tracking
  const [firstPhotoTaken, setFirstPhotoTaken] = useState(false);
  
  // ✅ New: Location tracking state
  const [currentLocation, setCurrentLocation] = useState(null);
  const [locationHistory, setLocationHistory] = useState([]);
  const [locationConfidence, setLocationConfidence] = useState(0);
  
  // ✅ Random delay settings for speech (3-5 seconds)
  const getRandomDelay = () => Math.floor(Math.random() * (5000 - 3000 + 1)) + 3000; // 3000-5000ms
  
  // ✅ Get current GT Node ID (manual input only) - REMOVED
  // const getCurrentGTNodeId = () => {
  //   return devGTNodeId || "";
  // };

  const setLogging = async (enabled) => {
    // Only handle stopping logging (keeping data)
    if (enabled) {
      console.log("Logging is automatically started after first photo");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/logging/set`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          provider: provider,
          enabled: false,
          run_id: currentRunId
        })
      });
      
      const result = await response.json();
      if (result.ok) {
        setLoggingEnabled(false);
        alert("Logging stopped. Data has been written to CSV files.");
      }
    } catch (e) {
      alert("Failed to stop logging.");
      console.error("Logging control error:", e);
    }
  };

  const checkLoggingStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/logging/status?session_id=${sessionId}&provider=${provider}`);
      const result = await response.json();
      if (result.ok) {
        setLoggingEnabled(result.state.enabled);
        setCurrentRunId(result.state.run_id || "");
      }
    } catch (e) {
      console.warn("Failed to check logging status:", e);
    }
  };

  // Check logging status - only on mount
  useEffect(() => {
    // Don't auto-check logging status since it's controlled by first photo
  }, []);

  const apiASR = async (blob) => {
    const mime = blob?.type || "audio/webm";
    const ext = extFromMime(mime);
    const fd = new FormData();
    fd.append("audio", blob, `rec.${ext}`);
    const r = await fetch(`${API_BASE}/api/asr`, { method:"POST", body:fd });
    if(!r.ok) throw new Error(`asr ${r.status}`); 
    return r.json();
  };

  // Helper functions
  const extFromMime = (mime) => {
    if(!mime) return "webm";
    if(mime.includes("webm")) return "webm";
    if(mime.includes("mp4")) return "m4a";
    if(mime.includes("aac")) return "aac";
    if(mime.includes("ogg")) return "ogg";
    if(mime.includes("wav")) return "wav";
    return "webm";
  };

  const compressImage = async (file, maxSide=1600, quality=0.85) => {
    const img = await new Promise((res, rej)=>{ 
      const u=URL.createObjectURL(file); 
      const el=new Image(); 
      el.onload=()=>res(el); 
      el.onerror=rej; 
      el.src=u; 
    });
    const canvas=document.createElement("canvas"); 
    const ctx=canvas.getContext("2d");
    const w=img.naturalWidth, h=img.naturalHeight; 
    const s=Math.min(1, maxSide/Math.max(w,h));
    canvas.width=Math.round(w*s); 
    canvas.height=Math.round(h*s); 
    ctx.drawImage(img,0,0,canvas.width,canvas.height);
    return await new Promise(res=>canvas.toBlob(b=>res(b),"image/jpeg",quality));
  };

  const pickBestMime = () => {
    const c=["audio/webm;codecs=opus","audio/webm","audio/mp4","audio/aac"]; 
    for(const x of c){ 
      if(window.MediaRecorder?.isTypeSupported?.(x)) return x; 
    } 
    return "audio/webm";
  };

  const onStart = async () => {
    unlock();                 // New: Unlock iOS audio
    setConnecting(true); setError("");
    try{
      const r = await apiStart({ session_id: sessionId, site_id: siteId, opening_provider: provider, lang });
      setStarted(true);
      // ✅ 确保对话框为空，不显示任何文字
      setMessages([]);
      // 重置第一次拍照状态
      setFirstPhotoTaken(false);
      // ✅ 重置位置追踪状态
      setCurrentLocation(null);
      setLocationHistory([]);
      setLocationConfidence(0);
      console.log("🔄 Session started, firstPhotoTaken reset to:", false);
      console.log("🔄 Location tracking reset");
      // 移除语音播报：speak(say);
    }catch(e){
      setError(e.message || String(e));
      alert(`Failed to start session: ${e.message || e}`);
    }finally{ setConnecting(false); }
  };

  const triggerCamera = ()=> fileInputRef.current?.click();
  const onPick = async (file)=>{
    if(!file) return;
    try{
      console.log("📸 onPick called, firstPhotoTaken:", firstPhotoTaken);
      // ✅ Check if this is the first photo
      if (!firstPhotoTaken) {
        console.log("📸 First photo detected, calling API with first_photo=false for direct detection");
        console.log("📸 Current state:", { firstPhotoTaken, siteId, provider });
        
        // First photo: call API with first_photo=false for direct detection (no preset output)
        const resp = await apiLocate(siteId, file, false); // false = not first photo, direct detection
        console.log("📸 First photo response:", resp);
        
        if (resp?.caption) {
          setMessages([{role:"assistant", text: resp.caption}]);
          // ✅ 修改：第一张照片直接检测，不播报预设输出
          console.log("📝 First photo detected and displayed (direct detection)");
          setFirstPhotoTaken(true);
          console.log("✅ First photo processed successfully with direct detection");
          
          // 🔧 Automatically start logging after first photo (warmup signal)
          console.log("🚀 First photo completed - starting data logging automatically");
          try {
            const runId = `${provider.toUpperCase()}-${siteId}-${Date.now()}`;
            await fetch(`${API_BASE}/api/logging/set`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                session_id: sessionId,
                provider: provider,
                enabled: true,
                run_id: runId
              })
            });
            setLoggingEnabled(true);
            setCurrentRunId(runId);
            console.log(`✅ Logging started automatically with run_id: ${runId}`);
          } catch (e) {
            console.warn("⚠️ Failed to start logging automatically:", e);
          }
          
          // ✅ New: Update location tracking after first photo
          if (resp.node_id) {
            setTimeout(() => {
              getSessionLocation();
            }, 1000); // Wait a bit for backend to process
          }
          
          // Display confidence metrics if available
          if (resp?.confidence !== undefined) {
            const confidenceMsg = `Top1: ${resp.node_id || 'None'}, Confidence: ${(resp.confidence * 100).toFixed(1)}%`;
            setMessages(m=>[...m,{role:"assistant", text: confidenceMsg}]);
            
            // Display margin information
            if (resp?.margin !== undefined) {
              const marginMsg = `Margin: ${(resp.margin * 100).toFixed(1)}% (${resp.low_conf ? 'Low' : 'High'} confidence)`;
              setMessages(m=>[...m,{role:"assistant", text: marginMsg}]);
              
              // ✅ New: RQ3 low confidence prompt for first photo
              if (resp.low_conf) {
                const photoConfirmationMsg = `Low confidence detected. Please continue taking photos to confirm your location.`;
                setMessages(m=>[...m,{role:"assistant", text: photoConfirmationMsg}]);
                
                // ✅ Add voice prompt for low confidence
                const delay = getRandomDelay();
                setTimeout(() => {
                  speak(photoConfirmationMsg);
                  console.log("🔊 Speaking low confidence photo confirmation prompt");
                }, delay);
              }
            }
          }
        } else {
          console.warn("⚠️ First photo response missing caption:", resp);
          // Fallback: try to get response directly
          console.log("🔄 Trying fallback approach...");
          const fallbackResp = await apiLocate(siteId, file, false);
          console.log("🔄 Fallback response:", fallbackResp);
        }
        return;
      }
      
      // Subsequent photos: normal BLIP matching
      const resp = await apiLocate(siteId, file, false); // false = not first photo
      const cap = resp?.caption || "";
      
      // Update last predicted node (system prediction)
      setLastPredictedNode(resp?.node_id || "");
      setLastGtNode(""); // GT will be manually recorded by experimenter
      
      // ✅ New: Auto-record system predicted node (except first photo)
      if (resp?.node_id) {
        console.log(`📝 System predicted node: ${resp.node_id} (will be logged automatically)`);
        // The system prediction is automatically logged in the backend via /api/locate
      }
      
      // ✅ New: RQ3 clarification session management
      if (resp?.clarification_id && !currentClarificationId) {
        setCurrentClarificationId(resp.clarification_id);
        setClarificationRoundCount(1); // First round is low confidence trigger
        console.log("Clarification session started:", resp.clarification_id);
      }
      
      // ✅ New: RQ3 error recovery detection - simplified
      // GT comparison will be done manually by experimenter
      
      // Display location description
      setMessages(m=>[...m,{role:"assistant", text: cap || "Location described."}]);
      if(cap) {
        // ✅ 修改：后续照片不自动播报，只显示文本
        console.log("📝 Subsequent photo output displayed (no auto-speak)");
      }
      
      // Display confidence metrics if available
      if (resp?.confidence !== undefined) {
        const confidenceMsg = `Top1: ${resp.node_id || 'None'}, Confidence: ${(resp.confidence * 100).toFixed(1)}%`;
        setMessages(m=>[...m,{role:"assistant", text: confidenceMsg}]);
        
        // ✅ New: Update location tracking after successful photo
        if (resp.node_id) {
          setTimeout(() => {
            getSessionLocation();
          }, 1000); // Wait a bit for backend to process
        }
        
        // Display margin information
        if (resp?.margin !== undefined) {
          const marginMsg = `Margin: ${(resp.margin * 100).toFixed(1)}% (${resp.low_conf ? 'Low' : 'High'} confidence)`;
          setMessages(m=>[...m,{role:"assistant", text: marginMsg}]);
          
          // ✅ New: RQ3 low confidence prompt - Modified for photo confirmation
          if (resp.low_conf) {
            const photoConfirmationMsg = `Low confidence detected. Please continue taking photos to confirm your location.`;
            setMessages(m=>[...m,{role:"assistant", text: photoConfirmationMsg}]);
            
            // ✅ Add voice prompt for low confidence
            const delay = getRandomDelay();
            setTimeout(() => {
              speak(photoConfirmationMsg);
              console.log("🔊 Speaking low confidence photo confirmation prompt");
            }, delay);
          }
        }
        
        // Display top candidates for debugging
        if (resp?.candidates && resp.candidates.length > 0) {
          const top3 = resp.candidates.slice(0, 3);
          const candidatesMsg = `Top candidates: ${top3.map(c => `${c.id}(${c.score.toFixed(3)})`).join(', ')}`;
          setMessages(m=>[...m,{role:"assistant", text: candidatesMsg}]);
          
          // Log detailed candidate info to console for debugging
          console.table(top3.map(c => ({
            id: c.id,
            score: c.score.toFixed(3),
            s_nl: c.s_nl?.toFixed(3) || 'N/A',
            s_struct: c.s_struct?.toFixed(3) || 'N/A',
            provider: c.provider || 'N/A'
            })));
        }
      }
      
    }catch(e){
      setMessages(m=>[...m,{role:"assistant", text: `Locate failed: ${e.message || e}` }]);
    }
  };

  const startRec = async ()=>{
    try{
      // ✅ 新增：点击Ask按钮时立即停止语音输出
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
        console.log("🔇 Voice output stopped when starting recording");
      }
      
      const mime = pickBestMime();
      const stream = await navigator.mediaDevices.getUserMedia({ audio:true });
      const rec = new MediaRecorder(stream, { mimeType: mime });
      chunksRef.current = [];
      rec.ondataavailable = (ev)=>{ if(ev.data && ev.data.size) chunksRef.current.push(ev.data); };
      rec.onstop = async ()=>{
        clearInterval(timerRef.current); setRecording(false);
        const blob = new Blob(chunksRef.current, { type: mime });
        stream.getTracks().forEach(t=>t.stop());
        await handleAudio(blob);
      };
      
      // Start recording
      rec.start(); 
      mediaRecorderRef.current = rec; 
      setRecording(true); 
      setDuration(0);
      timerRef.current = setInterval(()=> setDuration(d=>d+1), 1000);
      
      // Auto-stop after 10 seconds or when silence is detected
      setTimeout(() => {
        if (recording && mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
          stopRec();
        }
      }, 10000);
      
    }catch(e){ alert("Microphone access denied or unsupported."); }
  };
  
  const stopRec = ()=>{ 
    if(mediaRecorderRef.current && mediaRecorderRef.current.state!=="inactive") {
      mediaRecorderRef.current.stop();
      console.log("🛑 Recording stopped");
    }
  };

  const handleAudio = async (blob)=>{
    try{
      const asr = await apiASR(blob); // { text }
      const text = asr?.text || "";
      if(text) setMessages(m=>[...m,{role:"you", text}]);
      
            // ✅ New: Check if this is a location inquiry
      const isLocationInquiry = text.toLowerCase().includes("where") && 
                               (text.toLowerCase().includes("am i") || 
                                text.toLowerCase().includes("i am") ||
                                text.toLowerCase().includes("location") ||
                                text.toLowerCase().includes("position") ||
                                text.toLowerCase().includes("where am i") ||
                                text.toLowerCase().includes("where i am") ||
                                text.toLowerCase().includes("where am i now") ||
                                text.toLowerCase().includes("where am i currently"));
      
      // ✅ New: Check if this is a navigation inquiry
      const isNavigationInquiry = text.toLowerCase().includes("how") && 
                                 (text.toLowerCase().includes("should i go") ||
                                  text.toLowerCase().includes("do i go") ||
                                  text.toLowerCase().includes("can i go") ||
                                  text.toLowerCase().includes("navigate") ||
                                  text.toLowerCase().includes("direction") ||
                                  text.toLowerCase().includes("way") ||
                                  text.toLowerCase().includes("route"));
      
      console.log(`🔍 Inquiry detection: text="${text}"`);
      console.log(`   Location inquiry: ${isLocationInquiry}`);
      console.log(`   Navigation inquiry: ${isNavigationInquiry}`);
      
      if (isLocationInquiry) {
          console.log("🎯 Location inquiry detected - processing...");
          
          // 如果是位置询问，检查是否是第一次询问
          const locationInquiryCount = parseInt(localStorage.getItem(`location_inquiry_${sessionId}`) || "0");
          const isFirstLocationInquiry = locationInquiryCount === 0;
          
          console.log(`📊 Location inquiry count: ${locationInquiryCount}, isFirst: ${isFirstLocationInquiry}`);
          
          // 增加询问计数
          localStorage.setItem(`location_inquiry_${sessionId}`, String(locationInquiryCount + 1));
          
          let locationMessage = "";
        
                  if (isFirstLocationInquiry) {
            console.log("🔊 First location inquiry - speaking preset output");
            
            // 第一次询问位置时，播报预设输出
            if (siteId === "SCENE_A_MS") {
              locationMessage = "Welcome to the Maker Space! You are currently at the entrance area. This is a creative workspace with 3D printers, workbenches, and various tools. You can see the yellow line on the floor which will guide you through the space. To your left is a QR code bookshelf, and to your right are component drawers and 3D printers. The space opens up to an atrium area ahead.";
            } else if (siteId === "SCENE_B_STUDIO") {
              locationMessage = "Welcome to the Studio! You are currently at the entrance area. This is a collaborative workspace with workstations, meeting areas, and equipment. You can see the yellow line on the floor which will guide you through the space. The area includes glass-walled meeting rooms, lounge areas, and storage zones. It's designed for team collaboration and creative work.";
            } else {
              locationMessage = "Welcome! You are at the entrance of this space. Please take some photos to help me understand your current location better.";
            }
            
            console.log(`📝 Generated message for ${siteId}: ${locationMessage.substring(0, 100)}...`);
          } else if (currentLocation && locationConfidence > 0.5) {
          // 后续询问且有拍照内容，基于拍照内容播报
          locationMessage = `Based on your photos, you are currently at: ${currentLocation}. Confidence: ${(locationConfidence * 100).toFixed(1)}%.`;
          console.log("🔊 Subsequent location inquiry with photos - speaking based on photo content");
        } else if (currentLocation) {
          // 后续询问有位置但置信度低
          locationMessage = `I can see you're near ${currentLocation}, but I'm not very confident (${(locationConfidence * 100).toFixed(1)}%). Please take more photos to help me locate you better.`;
          console.log("🔊 Subsequent location inquiry with low confidence - asking for more photos");
        } else {
          // 后续询问但没有拍照内容，要求拍照确认
          locationMessage = "I need you to take some photos first so I can give you an accurate location update. Please take a few photos of your surroundings.";
          console.log("🔊 Subsequent location inquiry without photos - asking for photo confirmation");
        }
        
        console.log(`📝 Final location message: ${locationMessage.substring(0, 100)}...`);
        
        setMessages(m=>[...m,{role:"assistant", text: locationMessage}]);
        
        // 播报位置信息
        setTimeout(() => {
          speak(locationMessage);
          console.log("🔊 Speaking location information based on inquiry");
        }, 100);
        
        console.log("✅ Location inquiry processing completed - returning early");
        return;
      }
      
      // ✅ New: Handle navigation inquiries
      if (isNavigationInquiry) {
        console.log("🧭 Navigation inquiry detected - processing...");
        
        let navigationMessage = "";
        
        if (currentLocation && locationConfidence > 0.5) {
          // 有拍照内容，基于照片给出具体导航建议
          if (siteId === "SCENE_A_MS") {
            navigationMessage = `Based on your photos, you're at ${currentLocation}. From here, you can follow the yellow line on the floor. If you want to reach the 3D printer area, walk straight ahead about 5 steps, then turn right. For the atrium area, continue straight along the yellow line for about 10 steps.`;
          } else if (siteId === "SCENE_B_STUDIO") {
            navigationMessage = `Based on your photos, you're at ${currentLocation}. From here, you can follow the yellow line on the floor. If you want to reach the workstation area, walk straight ahead about 6 steps. For the glass meeting rooms, turn right and follow the path for about 8 steps.`;
          } else {
            navigationMessage = `Based on your photos, you're at ${currentLocation}. I can see your surroundings clearly now. Please let me know your destination and I'll provide specific navigation instructions.`;
          }
          
          console.log("🧭 Navigation inquiry with photos - giving specific guidance");
        } else {
          // 没有拍照内容，给出通用导航指导
          navigationMessage = `To proceed effectively, focus on moving towards the nearest open space or pathway that appears to lead to a more recognizable area. Since your orientation is unknown, start by facing forward. Walk straight ahead for about ten steps, then turn right and continue for another ten steps. If your surroundings still seem unclear after moving, consider taking a photo to help identify your location.`;
          
          console.log("🧭 Navigation inquiry without photos - giving general guidance");
        }
        
        console.log(`📝 Final navigation message: ${navigationMessage.substring(0, 100)}...`);
        
        setMessages(m=>[...m,{role:"assistant", text: navigationMessage}]);
        
        // 播报导航信息
        setTimeout(() => {
          speak(navigationMessage);
          console.log("🔊 Speaking navigation guidance");
        }, 100);
        
        console.log("✅ Navigation inquiry processing completed - returning early");
        return;
      }
      
      // ✅ New: Check confidence before allowing other navigation queries
      if (locationConfidence <= 0.7 && locationConfidence > 0) {
        const lowConfMsg = `Low confidence (${(locationConfidence * 100).toFixed(1)}%). Please take photos to confirm your location first.`;
        setMessages(m=>[...m,{role:"assistant", text: lowConfMsg}]);
        
        // Voice prompt for low confidence
        setTimeout(() => {
          speak(lowConfMsg);
          console.log("🔊 Speaking low confidence navigation block message");
        }, 100);
        return;
      }
      
      const qa = await apiQA({ session_id: sessionId, text, lang });
      const a = qa?.say?.[0] || qa?.answer || "";
      if(a) setMessages(m=>[...m,{role:"assistant", text:a}]);
      
      // ✅ 新增：RQ3 澄清对话记录
      if (currentClarificationId && text && a) {
        await recordClarificationRound(text, a, lastPredictedNode);
      }
      
      // iOS 从录音切回扬声器需要一点时间
      await speak(a, { delay: 350 });
    }catch(e){
      setMessages(m=>[...m,{role:"assistant", text:`ASR/QA failed: ${e.message || e}` }]);
    }
  };

  // --- layout ---
  const container = { maxWidth: 520, margin: "0 auto", padding: "16px" };
  const topBar = { fontSize: 14, color: "#111", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 };
  const input = { border: "1px solid #ccc", borderRadius: 10, padding: "10px 12px", fontSize: 16 };
  const bigStart = { width: "40vw", maxWidth: 260, minWidth: 180, height: 56, borderRadius: 16, fontSize: 22, fontWeight: 700, display: "block", margin: "24vh auto 0", background: "#111", color: "#fff", border: 0 };
  const dialog = { position: "relative", marginTop: 16, background: "#fff", border: "1px solid #ddd", borderRadius: 16, padding: 16, minHeight: "38vh", maxHeight: "55vh", overflowY: "auto", fontSize: 18, lineHeight: 1.6 };
  const closeBtn = { position:"absolute", right: 12, top: 12, width: 28, height: 28, borderRadius: 999, background: "#ff4d4f", color: "#fff", border: 0, fontWeight: 700 };
  const bottomBar = { display: "flex", gap: 12, justifyContent: "center", marginTop: 12 };
  const action = { width: "25vw", minWidth: 120, height: 56, borderRadius: 16, fontSize: 20, fontWeight: 700, border: "2px solid #111", background: "#fff" };

  return (
    <div style={{ minHeight: "100dvh", background: "#f5f6f8" }}>
      <main style={container}>
        {/* Top developer controls (small, at very top) */}
        <div style={topBar} aria-label="developer controls">
          <div>
            <label style={srOnly} htmlFor="lang">Language</label>
            <select id="lang" value={lang} onChange={e=>setLang(e.target.value)} style={input} aria-label="Language">
              <option value="en">English</option>
              <option value="zh">中文</option>
            </select>
          </div>
          <div>
            <label style={srOnly} htmlFor="session">Session</label>
            <input id="session" value={sessionId} onChange={e=>setSessionId(e.target.value)} style={input} aria-label="Session" />
          </div>
          <div>
            <label style={srOnly} htmlFor="provider">Provider</label>
            <select id="provider" value={provider} onChange={e=>setProvider(e.target.value)} style={input} aria-label="Provider">
              <option value="ft">ft</option>
              <option value="base">base</option>
            </select>
          </div>
          <div>
            <label style={srOnly} htmlFor="site">Site</label>
            <select id="site" value={siteId} onChange={e=>setSiteId(e.target.value)} style={input} aria-label="Site">
              <option value="SCENE_A_MS">SCENE_A_MS</option>
              <option value="SCENE_B_STUDIO">SCENE_B_STUDIO</option>
            </select>
          </div>
        </div>
        
        {/* Development controls row */}
        <div style={{...topBar, marginTop: 8, fontSize: 12}} aria-label="development controls">
          <div>
            <button 
              style={{...input, fontSize: 12, background: showDevInfo ? "#e6f3ff" : "#fff"}}
              onClick={()=>setShowDevInfo(!showDevInfo)}
              aria-label="Toggle development info"
            >
              {showDevInfo ? "Hide Dev" : "Show Dev"}
            </button>
          </div>
          <div>
            <span style={{fontSize: 11, opacity: 0.7}}>
              Provider: {provider} | Session: {sessionId}
            </span>
          </div>
          <div>
            <span style={{fontSize: 11, opacity: 0.7, color: "#0066cc"}}>
              GT: Will be manually recorded by experimenter
            </span>
          </div>
        </div>
        
        {/* ✅ New: Logging control buttons */}
        <div style={{...topBar, marginTop: 8, fontSize: 12}} aria-label="logging controls">
          <div>
            <span style={{fontSize: 11, opacity: 0.7, color: loggingEnabled ? "#4CAF50" : "#666"}}>
              Status: {loggingEnabled ? "Recording" : "Stopped"}
            </span>
          </div>
          <div>
            <button 
              onClick={()=>setLogging(false)} 
              style={{
                ...input,
                fontSize: 12, 
                backgroundColor: "#f44336",
                color: "white",
                border: "none",
                cursor: "pointer"
              }}
              disabled={!loggingEnabled}
              aria-label="Keep data logging and write to CSV"
            >
              Keep Logging
            </button>
          </div>
          <div>
            <span style={{fontSize: 11, opacity: 0.7, color: "#666"}}>
              First photo automatically starts logging
            </span>
          </div>

        </div>

        {!started ? (
          <button style={bigStart} aria-label="Start" onClick={onStart} disabled={connecting}>
            {connecting ? "Starting…" : "Start"}
          </button>
        ) : (
          <>
            <section style={dialog} role="region" aria-label="conversation">
              <button style={closeBtn} onClick={()=>{
                // Immediately stop voice broadcast
                if (window.speechSynthesis) {
                  window.speechSynthesis.cancel();
                }
                setStarted(false);
                setMessages([]);
                setFirstPhotoTaken(false); // Reset first photo state
                // ✅ 重置位置追踪状态
                setCurrentLocation(null);
                setLocationHistory([]);
                setLocationConfidence(0);
                console.log("🔄 Session closed, firstPhotoTaken reset to:", false);
                console.log("🔄 Location tracking reset");
              }} aria-label="Exit">
                ×
              </button>
              {messages.length === 0 && <div style={{opacity: 0.5, fontStyle: 'italic'}}>Take a photo to start exploring...</div>}
              {messages.map((m, i)=> (
                <div key={i} style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 12, opacity: .6 }}>{m.role === "you" ? "You" : "Assistant"}</div>
                  <div>{m.text}</div>
                </div>
              ))}
            </section>

            <div style={bottomBar}>
              <button 
                style={{
                  ...action, 
                  height: 58, // 44pt minimum for accessibility (1pt ≈ 1.33px)
                  minHeight: 58,
                  padding: "12px 16px"
                }} 
                onClick={triggerCamera} 
                aria-label="Take a photo to localize your position"
              >
                Photo
              </button>
              <input ref={fileInputRef} type="file" accept="image/*" capture="environment" style={{ display:"none" }} onChange={(e)=> onPick(e.target.files?.[0] || null)} />
              <button
                style={{
                  ...action, 
                  height: 58, // 44pt minimum for accessibility (1pt ≈ 1.33px)
                  minHeight: 58,
                  padding: "12px 16px",
                  background: recording?"#ffeded":"#fff"
                }}
                aria-label={recording ? `Stop recording, currently recording for ${duration} seconds` : "Start voice recording to ask questions"}
                onClick={recording ? stopRec : startRec}
              >
                {recording ? `Stop Recording (${duration}s)` : "Ask"}
              </button>
            </div>
            
            {/* ✅ New: Location status display */}
            {currentLocation && (
              <div style={{...topBar, marginTop: 8, fontSize: 12, background: "#f0f8ff", padding: "8px", borderRadius: "8px"}} aria-label="location status">
                <div>
                  <span style={{fontSize: 11, opacity: 0.8, color: "#0066cc"}}>
                    📍 Current: {currentLocation}
                  </span>
                </div>
                <div>
                  <span style={{fontSize: 11, opacity: 0.8, color: "#0066cc"}}>
                    🎯 Confidence: {(locationConfidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span style={{fontSize: 11, opacity: 0.8, color: "#0066cc"}}>
                    📊 History: {locationHistory.length} locations
                  </span>
                </div>
              </div>
            )}
            
            {/* ✅ New: Location verification and navigation controls - Only show when confidence is high */}
            {currentLocation && locationConfidence > 0.7 && (
              <div style={{...topBar, marginTop: 8, fontSize: 12, background: "#fff3cd", padding: "8px", borderRadius: "8px"}} aria-label="location controls">
                <div>
                  <button
                    onClick={() => verifyLocation()}
                    style={{
                      ...input,
                      fontSize: 10,
                      backgroundColor: "#ffc107",
                      color: "white",
                      border: "none",
                      cursor: "pointer",
                      padding: "4px 8px"
                    }}
                    aria-label="Verify current location"
                  >
                    Verify Location
                  </button>
                </div>
                <div>
                  <span style={{fontSize: 11, opacity: 0.8, color: "#856404"}}>
                    📍 Location tracking active
                  </span>
                </div>
                <div>
                  <span style={{fontSize: 11, opacity: 0.8, color: "#856404"}}>
                    🎯 Ask questions for navigation
                  </span>
                </div>
              </div>
            )}
            
            {/* ✅ New: Low confidence prompt - Encourage photo confirmation */}
            {currentLocation && locationConfidence <= 0.7 && locationConfidence > 0 && (
              <div style={{...topBar, marginTop: 8, fontSize: 12, background: "#fff0f0", padding: "8px", borderRadius: "8px"}} aria-label="low confidence prompt">
                <div>
                  <span style={{fontSize: 11, opacity: 0.8, color: "#d63384"}}>
                    ⚠️ Low confidence ({(locationConfidence * 100).toFixed(1)}%)
                  </span>
                </div>
                <div>
                  <span style={{fontSize: 11, opacity: 0.8, color: "#d63384"}}>
                    📸 Please continue taking photos to confirm location
                  </span>
                </div>
                <div>
                  <span style={{fontSize: 11, opacity: 0.8, color: "#d63384"}}>
                    🎯 Navigation function temporarily unavailable
                  </span>
                </div>
              </div>
            )}

            {/* Test Voice Button for iOS debugging */}
            <div style={{ textAlign: "center", marginTop: 8 }}>
              <button
                style={{ border: '1px solid #ccc', borderRadius: 12, padding: '6px 10px', fontSize: 14 }}
                onClick={() => { unlock(); speak('Voice test OK.'); }}
                aria-label="Test voice synthesis"
              >
                Test Voice
              </button>
            </div>

            {error && <div style={{ color:"#c00", marginTop: 8 }}>{error}</div>}
          </>
        )}

        <div style={{ marginTop: 16, fontSize: 12, opacity: .6 }}>API: {API_BASE ? API_BASE : "/api"}</div>
      </main>
    </div>
  );
}