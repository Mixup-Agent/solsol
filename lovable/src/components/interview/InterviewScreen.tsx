import { useEffect, useMemo, useRef, useState } from "react";
import { Mic, MicOff, RotateCcw, Square, Sparkles, Clock, Volume2, Eraser } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { API_BASE, createAudioTurn, createFirstTurn } from "@/lib/api";
import { interviewers, systemMessages, type Interviewer, type InterviewerType } from "@/lib/interview-mock";

interface Props {
  company: string;
  role: string;
  sessionId: string;
  onEnd: () => void;
}

const TOTAL_QUESTIONS = 6;
const AGENT_TO_INTERVIEWER: Record<string, InterviewerType> = {
  resume: "document",
  trend: "news",
  stress: "followup",
  judge: "fit",
};
const AGENT_TYPE_LABEL: Record<string, string> = {
  resume: "서류 기반",
  trend: "뉴스 기반",
  stress: "꼬리질문",
  judge: "종합 평가",
};

type SpeechRecognitionResultLike = {
  isFinal: boolean;
  0: { transcript: string };
};

type SpeechRecognitionEventLike = {
  resultIndex: number;
  results: ArrayLike<SpeechRecognitionResultLike>;
};

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
};

type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

type BrowserWithSpeech = Window & {
  SpeechRecognition?: SpeechRecognitionCtor;
  webkitSpeechRecognition?: SpeechRecognitionCtor;
};

function formatTime(s: number) {
  const m = Math.floor(s / 60).toString().padStart(2, "0");
  const sec = (s % 60).toString().padStart(2, "0");
  return `${m}:${sec}`;
}

function InterviewerPanel({
  p,
  active,
  isSpeaking,
}: {
  p: Interviewer;
  active: boolean;
  isSpeaking: boolean;
}) {
  return (
    <div
      className={`group relative aspect-[4/3] overflow-hidden rounded-2xl border bg-card transition-all duration-300 sm:aspect-video ${
        active ? "border-primary/50 glow-ring" : "border-border shadow-soft"
      }`}
    >
      {/* Stage background */}
      <div
        className={`absolute inset-0 transition-all duration-500 ${
          active ? "opacity-100" : "opacity-60 grayscale-[40%]"
        }`}
        style={{
          background: `radial-gradient(120% 80% at 50% 0%, ${p.accent} 0%, oklch(0.97 0.005 247) 70%)`,
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black/5 to-transparent" />

      {/* Avatar */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className={`relative transition-transform duration-500 ${active ? "scale-105" : "scale-95"}`}>
          <img
            src={p.avatar}
            alt={p.name}
            className={`h-[72px] w-[72px] rounded-full object-cover shadow-md sm:h-[88px] sm:w-[88px] ${active ? "" : "opacity-70 grayscale-[25%]"}`}
            loading="lazy"
            width={88}
            height={88}
          />
          {active && isSpeaking && (
            <>
              <span className="absolute inset-0 rounded-full ring-2 ring-white/40" />
              <span className="absolute -inset-2 animate-ping rounded-full bg-primary/15" />
            </>
          )}
        </div>
      </div>

      {/* Top-left status */}
      <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-sm">
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            active ? (isSpeaking ? "bg-red-400 pulse-dot" : "bg-emerald-400") : "bg-white/50"
          }`}
        />
        {active ? (isSpeaking ? "REC" : "LIVE") : "대기"}
      </div>

      {/* Bottom name plate */}
      <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-2 bg-gradient-to-t from-black/70 via-black/30 to-transparent p-3 pt-8">
        <div className="min-w-0">
          <p className="truncate text-[13px] font-semibold text-white sm:text-sm">{p.name}</p>
          <p className="truncate text-[11px] text-white/75 sm:text-xs">{p.role}</p>
        </div>
        {active && isSpeaking && (
          <div className="flex items-end gap-0.5">
            {[0, 1, 2, 3].map((i) => (
              <span
                key={i}
                className="w-0.5 rounded-full bg-white wave-bar"
                style={{ height: `${6 + (i % 2) * 4}px`, animationDelay: `${i * 90}ms` }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function InterviewScreen({ company, role, sessionId, onEnd }: Props) {
  const [roundNo, setRoundNo] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isBooting, setIsBooting] = useState(true);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [currentAgentType, setCurrentAgentType] = useState("resume");
  const [recordedAudio, setRecordedAudio] = useState<Blob | null>(null);
  const [lastTtsAudioUrl, setLastTtsAudioUrl] = useState<string | null>(null);
  const [transcript, setTranscript] = useState("");
  const [systemMsg, setSystemMsg] = useState(systemMessages[0]);
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const speechRef = useRef<SpeechRecognitionLike | null>(null);
  const speechFinalRef = useRef("");
  const canUseSpeechRef = useRef(false);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [speechSupported, setSpeechSupported] = useState(false);

  const currentInterviewerId = AGENT_TO_INTERVIEWER[currentAgentType] ?? "document";
  const currentInterviewer = useMemo(
    () => interviewers.find((i) => i.id === currentInterviewerId)!,
    [currentInterviewerId]
  );

  useEffect(() => {
    const t = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const browser = window as BrowserWithSpeech;
    const Ctor = browser.SpeechRecognition || browser.webkitSpeechRecognition;
    if (!Ctor) {
      setSpeechSupported(false);
      return;
    }
    setSpeechSupported(true);
    canUseSpeechRef.current = true;
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;

    const boot = async () => {
      setIsBooting(true);
      setError(null);
      setSystemMsg("면접 첫 질문을 준비 중입니다");
      try {
        const first = await createFirstTurn(sessionId);
        if (cancelled) return;
        setCurrentQuestion(first.question);
        setCurrentAgentType(first.agent_type);
        setRoundNo(first.round_no);
        if (first.tts_audio_url) {
          await playTts(first.tts_audio_url);
        }
      } catch (e) {
        if (!cancelled) setError("첫 질문을 불러오지 못했습니다.");
      } finally {
        if (!cancelled) setIsBooting(false);
      }
    };

    void boot();
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
        audioRef.current = null;
      }
      speechRef.current?.stop();
    };
  }, [sessionId]);

  const pickMimeType = () => {
    const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
    for (const mime of candidates) {
      if (window.MediaRecorder?.isTypeSupported?.(mime)) return mime;
    }
    return "";
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      setRecordedAudio(null);
      setTranscript("");
      setLiveTranscript("");
      speechFinalRef.current = "";
      setError(null);

      const mimeType = pickMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        setRecordedAudio(blob);
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        setSystemMsg("답변이 녹음되었습니다. 답변 완료를 눌러 전송하세요.");
      };

      recorder.start();
      setIsRecording(true);
      setSystemMsg("답변을 듣고 있습니다");

      if (canUseSpeechRef.current) {
        const browser = window as BrowserWithSpeech;
        const Ctor = browser.SpeechRecognition || browser.webkitSpeechRecognition;
        if (Ctor) {
          const speech = new Ctor();
          speechRef.current = speech;
          speech.lang = "ko-KR";
          speech.continuous = true;
          speech.interimResults = true;
          speech.onresult = (event: SpeechRecognitionEventLike) => {
            let finalTextChunk = "";
            let interimText = "";
            for (let i = event.resultIndex; i < event.results.length; i += 1) {
              const result = event.results[i];
              const text = result?.[0]?.transcript ?? "";
              if (result?.isFinal) finalTextChunk += text;
              else interimText += text;
            }
            if (finalTextChunk) {
              speechFinalRef.current = `${speechFinalRef.current} ${finalTextChunk}`.trim();
            }
            setLiveTranscript(`${speechFinalRef.current} ${interimText}`.trim());
          };
          speech.onerror = () => {
            setSystemMsg("음성 인식이 불안정합니다. 녹음은 계속됩니다.");
          };
          speech.start();
        }
      }
    } catch (e) {
      setError("마이크 접근에 실패했습니다. 브라우저 권한을 확인해 주세요.");
    }
  };

  const stopRecording = () => {
    if (!recorderRef.current || recorderRef.current.state !== "recording") return;
    recorderRef.current.stop();
    speechRef.current?.stop();
    setIsRecording(false);
  };

  const toggleRecord = () => {
    if (isSpeaking || isSubmitting || isBooting) return;
    if (isRecording) {
      stopRecording();
    } else {
      void startRecording();
    }
  };

  const playTts = async (ttsAudioUrl: string) => {
    // 이전 오디오가 재생 중이면 즉시 중단
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }
    setIsSpeaking(false);

    const src = `${API_BASE}${ttsAudioUrl}`;
    setLastTtsAudioUrl(src);
    setIsSpeaking(true);
    return new Promise<void>((resolve) => {
      const audio = new Audio(src);
      audioRef.current = audio;
      audio.onended = () => {
        setIsSpeaking(false);
        resolve();
      };
      audio.onerror = () => {
        setIsSpeaking(false);
        resolve();
      };
      void audio.play().catch(() => {
        setIsSpeaking(false);
        resolve();
      });
    });
  };

  const submitAnswer = async () => {
    if (isSubmitting || !currentQuestion) return;
    if (isRecording) {
      stopRecording();
      setSystemMsg("녹음을 종료했습니다. 답변 완료를 다시 눌러 전송하세요.");
      return;
    }
    if (!recordedAudio) {
      setError("먼저 녹음을 완료해 주세요.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSystemMsg("음성 인식 및 다음 질문 생성 중입니다");
    setTranscript(liveTranscript.trim());

    const ext = recordedAudio.type.includes("mp4") ? "m4a" : "webm";
    const formData = new FormData();
    formData.append("audio_file", recordedAudio, `answer.${ext}`);
    formData.append("round_no", String(roundNo + 1));
    formData.append("question_text", currentQuestion);
    formData.append("agent_type", currentAgentType);

    try {
      const result = await createAudioTurn(sessionId, formData);
      if (result.stt_status !== "success") {
        setError(result.stt_error ?? "음성 인식에 실패했습니다.");
        setTranscript("");
        return;
      }

      setTranscript(result.transcript);
      setLiveTranscript("");
      setCurrentQuestion(result.next_question);
      setCurrentAgentType(result.next_agent_type ?? currentAgentType);
      setRoundNo((prev) => prev + 1);
      setRecordedAudio(null);
      setSystemMsg(systemMessages[(roundNo + 1) % systemMessages.length]);

      if (result.tts_audio_url) {
        await playTts(result.tts_audio_url);
      }

      if (roundNo + 1 >= TOTAL_QUESTIONS) {
        onEnd();
      }
    } catch (e) {
      setError("답변 처리에 실패했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const replay = () => {
    if (!lastTtsAudioUrl || isSpeaking) return;
    setIsSpeaking(true);
    const audio = new Audio(lastTtsAudioUrl);
    audioRef.current = audio;
    audio.onended = () => setIsSpeaking(false);
    audio.onerror = () => setIsSpeaking(false);
    void audio.play().catch(() => setIsSpeaking(false));
  };

  const clearAnswer = () => {
    if (isRecording) {
      stopRecording();
    }
    setTranscript("");
    setLiveTranscript("");
    setRecordedAudio(null);
    setError(null);
    setSystemMsg("답변을 지웠습니다. 다시 녹음해 주세요.");
  };

  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4">
          <div className="min-w-0">
            <p className="truncate text-xs text-muted-foreground sm:text-sm">{company}</p>
            <p className="truncate text-sm font-semibold text-foreground sm:text-[15px]">{role}</p>
          </div>
          <div className="flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1.5 shadow-soft sm:px-4 sm:py-2">
            <Clock className="h-3.5 w-3.5 text-muted-foreground sm:h-4 sm:w-4" />
            <span className="font-mono text-sm font-semibold tabular-nums text-foreground sm:text-[15px]">{formatTime(elapsed)}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden text-xs font-medium text-muted-foreground sm:inline">
              질문 {Math.min(roundNo + 1, TOTAL_QUESTIONS)} / {TOTAL_QUESTIONS}
            </span>
            <Badge className="rounded-full bg-success/15 px-2.5 py-1 text-xs text-success hover:bg-success/15 sm:px-3">
              <span className="mr-1 h-1.5 w-1.5 rounded-full bg-success pulse-dot" />
              진행 중
            </Badge>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-4 py-5 sm:px-6 sm:py-6">
        {/* System status */}
        <div className="mb-4 flex items-center justify-between gap-2 sm:mb-5">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-accent/70 px-3 py-1 text-xs text-accent-foreground">
            <Sparkles className="h-3 w-3" />
            {systemMsg}
          </div>
          <span className="text-xs text-muted-foreground sm:hidden">
            {Math.min(roundNo + 1, TOTAL_QUESTIONS)} / {TOTAL_QUESTIONS}
          </span>
        </div>

        {/* Interviewer video grid */}
        <div className="grid grid-cols-2 gap-2 sm:gap-3">
          {interviewers.map((p) => (
            <InterviewerPanel
              key={p.id}
              p={p}
              active={p.id === currentInterviewer.id}
              isSpeaking={isSpeaking}
            />
          ))}
        </div>

        {/* Current question */}
        <div className="mt-5 rounded-3xl border border-border bg-card p-5 shadow-card fade-in sm:p-7">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="rounded-full bg-accent text-accent-foreground">
              {AGENT_TYPE_LABEL[currentAgentType] ?? "면접 질문"}
            </Badge>
            <span className="text-sm text-muted-foreground">{currentInterviewer.name}</span>
            {isSpeaking && (
              <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                <Volume2 className="h-3 w-3" />
                질문 중
              </span>
            )}
          </div>
          <p className="mt-3 text-[19px] font-semibold leading-[1.4] tracking-tight text-foreground sm:mt-4 sm:text-[22px]">
            {currentQuestion || "첫 질문을 준비하고 있습니다..."}
          </p>
        </div>

        {/* Voice recorder card */}
        <div className="mt-3 overflow-hidden rounded-3xl border border-border bg-card shadow-card sm:mt-4">
          {/* Top: recorder strip */}
          <div className="flex items-center gap-4 border-b border-border bg-surface-muted/60 px-5 py-5 sm:px-7">
            <button
              onClick={toggleRecord}
              disabled={isSpeaking || isSubmitting || isBooting}
              aria-label={isRecording ? "녹음 중지" : "녹음 시작"}
              className={`relative flex h-14 w-14 shrink-0 items-center justify-center rounded-full text-white transition-all disabled:cursor-not-allowed disabled:opacity-40 sm:h-16 sm:w-16 ${
                isRecording
                  ? "bg-destructive shadow-[0_0_0_3px_oklch(0.6_0.2_25/0.10)]"
                  : "bg-primary hover:scale-105 hover:shadow-glow"
              }`}
            >
              {isRecording ? <MicOff className="h-5 w-5 sm:h-6 sm:w-6" /> : <Mic className="h-5 w-5 sm:h-6 sm:w-6" />}
              {isRecording && <span className="absolute inset-0 animate-ping rounded-full bg-destructive/30" />}
            </button>

            <div className="min-w-0 flex-1">
              <p className="truncate text-[15px] font-semibold text-foreground">
                {isRecording
                  ? "답변을 듣고 있어요"
                  : isSpeaking
                  ? "면접관이 질문 중입니다"
                  : isSubmitting
                  ? "답변을 분석하고 있습니다"
                  : "마이크를 눌러 답변을 시작하세요"}
              </p>
              <div className="mt-2 flex h-7 items-center gap-[3px]">
                {isRecording ? (
                  Array.from({ length: 32 }).map((_, i) => (
                    <span
                      key={i}
                      className="w-[3px] rounded-full bg-primary wave-bar"
                      style={{
                        height: `${8 + ((i * 11) % 18)}px`,
                        animationDelay: `${i * 55}ms`,
                      }}
                    />
                  ))
                ) : isSpeaking ? (
                  <span className="text-xs text-muted-foreground">면접관이 다음 질문을 준비하고 있어요.</span>
                ) : isSubmitting ? (
                  <span className="text-xs text-muted-foreground">STT/TTS 처리 중입니다...</span>
                ) : (
                  <span className="text-xs text-muted-foreground">마이크 준비 완료 · STT 자동 변환</span>
                )}
              </div>
            </div>

            <div className="hidden shrink-0 items-center gap-2 sm:flex">
              <Button variant="outline" size="sm" onClick={replay} className="h-10 rounded-xl">
                <RotateCcw className="mr-1 h-3.5 w-3.5" />
                다시 듣기
              </Button>
            </div>
          </div>

          {/* Transcript */}
          <div className="px-5 py-5 sm:px-7">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                실시간 변환 (STT)
              </p>
              {transcript && (
                <span className="text-xs text-muted-foreground">{transcript.length}자</span>
              )}
            </div>
            <p className="mt-2 min-h-[4.5rem] text-[16px] leading-[1.4] text-foreground">
              {transcript || (
                <span className="text-muted-foreground">
                  {liveTranscript
                    ? liveTranscript
                    : recordedAudio
                    ? "답변 준비 완료. '답변 완료'를 눌러 전송하세요."
                    : "마이크를 누르면 답변이 텍스트로 기록됩니다."}
                </span>
              )}
              {isRecording && (
                <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-primary align-middle" />
              )}
            </p>

            {/* Action row */}
            <div className="mt-5 flex flex-wrap items-center justify-between gap-2 border-t border-border pt-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={onEnd}
                className="h-10 rounded-xl px-3 text-muted-foreground hover:text-destructive"
              >
                <Square className="mr-1 h-3.5 w-3.5" />
                면접 종료
              </Button>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={replay} className="h-10 rounded-xl sm:hidden">
                  <RotateCcw className="mr-1 h-3.5 w-3.5" />
                  다시 듣기
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearAnswer}
                  disabled={isSubmitting || (!recordedAudio && !transcript && !liveTranscript && !isRecording)}
                  className="h-10 rounded-xl"
                >
                  <Eraser className="mr-1 h-3.5 w-3.5" />
                  답변 지우기
                </Button>
                <Button
                  onClick={submitAnswer}
                  disabled={isSubmitting || !currentQuestion || (!recordedAudio && !isRecording)}
                  className="h-10 rounded-xl px-5 font-semibold"
                >
                  {isSubmitting ? "처리 중..." : "답변 완료"}
                </Button>
              </div>
            </div>
            {!speechSupported && (
              <p className="mt-3 text-xs text-muted-foreground">
                브라우저 실시간 STT를 지원하지 않습니다. 녹음 후 서버 STT 결과가 표시됩니다.
              </p>
            )}
            {error && (
              <p className="mt-3 rounded-xl border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
