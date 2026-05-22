import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { finalizeInterview } from "@/lib/api";

interface Props {
  sessionId: string;
  onDone: () => void;
}

const steps = [
  "답변 구조 분석",
  "직무 적합성 평가",
  "꼬리질문 대응력 분석",
  "개선 포인트 정리",
];

export function AnalyzingScreen({ sessionId, onDone }: Props) {
  const [progress, setProgress] = useState(0);
  const [finalized, setFinalized] = useState(false);

  useEffect(() => {
    const t = setInterval(() => {
      setProgress((p) => (p >= steps.length ? p : p + 1));
    }, 900);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!sessionId) {
      setFinalized(true);
      return;
    }
    finalizeInterview(sessionId)
      .then(() => setFinalized(true))
      .catch(() => setFinalized(true));
  }, [sessionId]);

  const ready = progress >= steps.length && finalized;

  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-12">
      <div className="w-full max-w-xl rounded-3xl border border-border bg-card p-8 shadow-card fade-in">
        <div className="text-center">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">모의면접이 종료되었습니다</h2>
          <p className="mt-2 text-[15px] text-muted-foreground">
            답변 흐름, 직무 적합성, 커뮤니케이션 역량을 분석하고 있어요.
          </p>
        </div>

        <ul className="mt-8 space-y-3">
          {steps.map((s, i) => {
            const done = i < progress;
            const active = i === progress && !ready;
            return (
              <li
                key={s}
                className={`flex items-center gap-3 rounded-2xl border px-4 py-3.5 transition ${
                  done ? "border-success/30 bg-success/5" : active ? "border-primary/30 bg-primary/5" : "border-border bg-surface-muted"
                }`}
              >
                <div className={`flex h-8 w-8 items-center justify-center rounded-full ${done ? "bg-success text-success-foreground" : active ? "bg-primary text-primary-foreground" : "bg-surface text-muted-foreground"}`}>
                  {done ? <Check className="h-4 w-4" /> : active ? <Loader2 className="h-4 w-4 animate-spin" /> : <span className="text-xs">{i + 1}</span>}
                </div>
                <p className={`text-[15px] ${done || active ? "text-foreground" : "text-muted-foreground"}`}>{s}</p>
              </li>
            );
          })}
        </ul>

        <Button onClick={onDone} disabled={!ready} className="mt-8 h-12 w-full rounded-2xl text-[15px] font-semibold">
          {ready ? "피드백 리포트 보기" : "분석 중..."}
        </Button>
      </div>
    </div>
  );
}
