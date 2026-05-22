import { useEffect, useState } from "react";
import { Mic, MicOff, RotateCcw, Square, Sparkles, Clock, Volume2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { interviewers, type Interviewer } from "@/lib/interview-mock";
import { startInterview, submitAnswer, finalizeInterview } from "@/lib/api";

interface Props {
  company: string;
  role: string;
  sessionId: string;
  onEnd: () => void;
}

const TOTAL_QUESTIONS = 8;

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
      <div
        className={`absolute inset-0 transition-all duration-500 ${
          active ? "opacity-100" : "opacity-60 grayscale-[40%]"
        }`}
        style={{
          background: `radial-gradient(120% 80% at 50% 0%, ${p.accent} 0%, oklch(0.97 0.005 247) 70%)`,
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black/5 to-transparent" />
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
      <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-black/40 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-sm">
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            active ? (isSpeaking ? "bg-red-400 pulse-dot" : "bg-emerald-400") : "bg-white/50"
          }`}
        />
        {active ? (isSpeaking ? "REC" : "LIVE") : "대기"}
      </div>
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

const AGENT_TO_INTERVIEWER: Record<string, string> = {
  resume: "document",
  trend: "news",
  stress: "followup",
  judge: "fit",
};

export function InterviewScreen({ company, role, sessionId, onEnd }: Props) {
  const [round, setRound] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [question, setQuestion] = useState("");
  const [activeAgent, setActiveAgent] = useState("resume");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeInterviewer =
    interviewers.find((i) => i.id === AGENT_TO_INTERVIEWER[activeAgent]) ?? interviewers[0];

  // 타이머
  useEffect(() => {
    const t = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, []);

  // 질문 도착 시 1.8초 speaking 애니메이션
  useEffect(() => {
    if (!question) return;
    setIsSpeaking(true);
    const t = setTimeout(() => setIsSpeaking(false), 1800);
    return () => clearTimeout(t);
  }, [question]);

  // 최초 마운트: /start 호출
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await startInterview(sessionId);
        if (cancelled) return;
        setQuestion(res.question);
        setRound(res.round);
        setActiveAgent(res.agent ?? "resume");
      } catch {
        if (!cancelled) setError("면접을 시작할 수 없습니다. 서버 연결을 확인해 주세요.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [sessionId]);

  const handleEnd = async () => {
    setSubmitting(true);
    try {
      await finalizeInterview(sessionId);
    } catch {
      // finalize 실패해도 리포트 화면으로 이동
    }
    onEnd();
  };

  const toggleRecord = () => {
    if (isSpeaking || loading || submitting) return;
    setIsRecording((r) => !r);
  };

  const handleSubmit = async () => {
    if (!transcript.trim() || submitting) return;
    setSubmitting(true);
    setIsRecording(false);
    setError(null);
    try {
      const res = await submitAnswer(sessionId, transcript);
      setTranscript("");
      setRound(res.round);
      if (res.is_done) {
        onEnd();
        return;
      }
      setQuestion(res.question ?? "");
      setActiveAgent(res.agent ?? "resume");
    } catch {
      setError("답변 제출에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setSubmitting(false);
    }
  };

  const replay = () => {
    setIsSpeaking(true);
    setTimeout(() => setIsSpeaking(false), 1500);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Loader2 className="h-8 w-8 animate-spin" />
          <p className="text-sm">면접관이 준비 중입니다...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
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
              질문 {round + 1} / {TOTAL_QUESTIONS}
            </span>
            <Badge className="rounded-full bg-success/15 px-2.5 py-1 text-xs text-success hover:bg-success/15 sm:px-3">
              <span className="mr-1 h-1.5 w-1.5 rounded-full bg-success pulse-dot" />
              진행 중
            </Badge>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-4 py-5 sm:px-6 sm:py-6">
        <div className="mb-4 flex items-center justify-between gap-2 sm:mb-5">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-accent/70 px-3 py-1 text-xs text-accent-foreground">
            <Sparkles className="h-3 w-3" />
            {activeAgent === "resume" && "이력서 기반 질문"}
            {activeAgent === "trend" && "트렌드 질문"}
            {activeAgent === "stress" && "압박 질문"}
          </div>
          <span className="text-xs text-muted-foreground sm:hidden">
            {round + 1} / {TOTAL_QUESTIONS}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:gap-3">
          {interviewers.map((p) => (
            <InterviewerPanel
              key={p.id}
              p={p}
              active={p.id === activeInterviewer.id}
              isSpeaking={isSpeaking}
            />
          ))}
        </div>

        <div className="mt-5 rounded-3xl border border-border bg-card p-5 shadow-card fade-in sm:p-7">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="rounded-full bg-accent text-accent-foreground">
              {activeAgent}
            </Badge>
            <span className="text-sm text-muted-foreground">{activeInterviewer.name}</span>
            {isSpeaking && (
              <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                <Volume2 className="h-3 w-3" />
                질문 중
              </span>
            )}
          </div>
          <p className="mt-3 text-[19px] font-semibold leading-[1.4] tracking-tight text-foreground sm:mt-4 sm:text-[22px]">
            {question}
          </p>
        </div>

        {error && (
          <p className="mt-3 rounded-2xl border border-destructive/30 bg-destructive/5 px-5 py-3 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="mt-3 overflow-hidden rounded-3xl border border-border bg-card shadow-card sm:mt-4">
          <div className="flex items-center gap-4 border-b border-border bg-surface-muted/60 px-5 py-5 sm:px-7">
            <button
              onClick={toggleRecord}
              disabled={isSpeaking || loading || submitting}
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
                {submitting
                  ? "답변 분석 중..."
                  : isRecording
                  ? "답변을 듣고 있어요"
                  : isSpeaking
                  ? "면접관이 질문 중입니다"
                  : "마이크를 눌러 답변을 시작하세요"}
              </p>
              <div className="mt-2 flex h-7 items-center gap-[3px]">
                {isRecording ? (
                  Array.from({ length: 32 }).map((_, i) => (
                    <span
                      key={i}
                      className="w-[3px] rounded-full bg-primary wave-bar"
                      style={{ height: `${8 + ((i * 11) % 18)}px`, animationDelay: `${i * 55}ms` }}
                    />
                  ))
                ) : isSpeaking ? (
                  <span className="text-xs text-muted-foreground">면접관이 다음 질문을 준비하고 있어요.</span>
                ) : (
                  <span className="text-xs text-muted-foreground">마이크 준비 완료 · 텍스트로 직접 입력도 가능합니다</span>
                )}
              </div>
            </div>

            <div className="hidden shrink-0 items-center gap-2 sm:flex">
              <Button variant="outline" size="sm" onClick={replay} disabled={submitting} className="h-10 rounded-xl">
                <RotateCcw className="mr-1 h-3.5 w-3.5" />
                다시 듣기
              </Button>
            </div>
          </div>

          <div className="px-5 py-5 sm:px-7">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                답변 입력
              </p>
              {transcript && (
                <span className="text-xs text-muted-foreground">{transcript.length}자</span>
              )}
            </div>
            <textarea
              className="mt-2 min-h-[4.5rem] w-full resize-none bg-transparent text-[16px] leading-[1.4] text-foreground outline-none placeholder:text-muted-foreground"
              placeholder="마이크를 누르거나 여기에 직접 답변을 입력하세요."
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              disabled={submitting}
              rows={3}
            />

            <div className="mt-5 flex flex-wrap items-center justify-between gap-2 border-t border-border pt-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleEnd}
                disabled={submitting}
                className="h-10 rounded-xl px-3 text-muted-foreground hover:text-destructive"
              >
                <Square className="mr-1 h-3.5 w-3.5" />
                면접 종료
              </Button>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={replay} disabled={submitting} className="h-10 rounded-xl sm:hidden">
                  <RotateCcw className="mr-1 h-3.5 w-3.5" />
                  다시 듣기
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={!transcript.trim() || submitting}
                  className="h-10 rounded-xl px-5 font-semibold"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      처리 중...
                    </>
                  ) : (
                    "답변 완료"
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
