import { useEffect, useState } from "react";
import { Lightbulb, RotateCcw, Save, Plus, TrendingUp, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { getReport } from "@/lib/api";

interface Props {
  company: string;
  role: string;
  sessionId: string;
  onRestart: () => void;
  onNew: () => void;
}

const SCORE_LABELS: Record<string, string> = {
  logic: "논리적 사고력",
  experience: "경험 구체성",
  trend: "산업·트렌드 이해도",
};

const practices = [
  "STAR 구조로 답변 재작성하기",
  "성과 수치화 연습",
  "지원 회사 최근 뉴스 3개 정리",
  "1분 자기소개 압축 연습",
];

type ReportData = Awaited<ReturnType<typeof getReport>>;

export function ReportScreen({ company, role, sessionId, onRestart, onNew }: Props) {
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    getReport(sessionId)
      .then(setData)
      .catch(() => setError("리포트를 불러오는 데 실패했습니다."))
      .finally(() => setLoading(false));
  }, [sessionId]);

  // Q&A 페어 추출
  const qaPairs = data
    ? data.messages.reduce<{ q: string; a: string; agent: string }[]>((acc, msg, i, arr) => {
        if (msg.role === "interviewer") {
          const next = arr[i + 1];
          acc.push({
            q: msg.content,
            a: next?.role === "candidate" ? next.content : "",
            agent: data.agent_history[acc.length] ?? "",
          });
        }
        return acc;
      }, [])
    : [];

  const scores = data
    ? Object.entries(data.scores).map(([key, value]) => ({
        key,
        label: SCORE_LABELS[key] ?? key,
        value: value as number,
      }))
    : [];

  const total = scores.length
    ? Math.round(scores.reduce((s, x) => s + x.value, 0) / scores.length)
    : 0;

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Loader2 className="h-8 w-8 animate-spin" />
          <p className="text-sm">리포트 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6">
        <div className="rounded-3xl border border-destructive/30 bg-destructive/5 p-8 text-center">
          <p className="text-[15px] text-destructive">{error ?? "데이터를 불러올 수 없습니다."}</p>
          <Button onClick={onNew} variant="outline" className="mt-4 rounded-xl">
            처음으로
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
      {/* Hero summary */}
      <div className="overflow-hidden rounded-3xl border border-border bg-card shadow-card fade-in">
        <div className="border-b border-border bg-gradient-to-br from-accent/40 to-transparent px-6 py-8 sm:px-10 sm:py-10">
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <span className="rounded-full bg-surface px-2.5 py-1 shadow-soft">면접 피드백 리포트</span>
            <span>{qaPairs.length}문항</span>
          </div>

          <div className="mt-5 grid grid-cols-1 items-end gap-8 sm:grid-cols-[1fr_auto]">
            <div>
              <h1 className="text-[28px] font-bold leading-tight tracking-tight text-foreground sm:text-[36px]">
                {company} · {role}
              </h1>
              <p className="mt-3 max-w-xl text-[16px] leading-[1.6] text-muted-foreground sm:text-[17px]">
                {data.feedback}
              </p>
            </div>

            <div className="flex items-end gap-4">
              <div className="text-right">
                <p className="text-xs font-medium text-muted-foreground">종합 점수</p>
                <p className="mt-0.5 text-5xl font-bold leading-none tracking-tight text-primary sm:text-6xl">
                  {total}
                  <span className="ml-0.5 text-xl font-medium text-muted-foreground">/100</span>
                </p>
                <p className="mt-1.5 inline-flex items-center gap-1 text-xs font-medium text-success">
                  <TrendingUp className="h-3 w-3" />
                  AI 평가 완료
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Score breakdown */}
        <div className="grid grid-cols-1 gap-x-8 gap-y-4 px-6 py-6 sm:grid-cols-3 sm:px-10 sm:py-7">
          {scores.map((s) => (
            <div key={s.key}>
              <div className="flex items-center justify-between">
                <span className="text-[15px] text-foreground">{s.label}</span>
                <span className="text-sm font-semibold tabular-nums text-foreground">{s.value}</span>
              </div>
              <Progress value={s.value} className="mt-2 h-1.5 rounded-full" />
            </div>
          ))}
        </div>
      </div>

      {/* Q&A 질문별 피드백 */}
      {qaPairs.length > 0 && (
        <div className="mt-5 rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-7">
          <h2 className="text-xl font-semibold tracking-tight text-foreground">질문별 답변 기록</h2>
          <p className="mt-1 text-sm text-muted-foreground">각 질문을 펼쳐 내 답변을 확인하세요.</p>
          <Accordion type="single" collapsible className="mt-4">
            {qaPairs.map((pair, i) => (
              <AccordionItem key={i} value={`q-${i}`} className="border-b border-border last:border-0">
                <AccordionTrigger className="py-4 text-left hover:no-underline">
                  <div className="flex flex-1 items-center gap-3 pr-3">
                    <Badge variant="secondary" className="shrink-0 rounded-full bg-accent text-accent-foreground">
                      Q{i + 1}
                    </Badge>
                    <span className="text-left text-[15px] font-medium leading-[1.4] text-foreground">{pair.q}</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-5">
                  <div className="rounded-2xl bg-surface-muted p-5">
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">내 답변</p>
                    <p className="mt-2 text-[15px] leading-[1.6] text-foreground">
                      {pair.a || <span className="text-muted-foreground">답변 없음</span>}
                    </p>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      )}

      {/* 추천 연습 */}
      <div className="mt-5 rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-7">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-accent-foreground">
            <Lightbulb className="h-4 w-4" />
          </div>
          <h2 className="text-xl font-semibold tracking-tight text-foreground">추천 연습</h2>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {practices.map((p, i) => (
            <div
              key={p}
              className="flex items-center gap-3 rounded-2xl border border-border bg-surface px-5 py-4 text-[15px] text-foreground transition hover:border-primary/40 hover:bg-accent/30"
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-semibold text-accent-foreground">
                {i + 1}
              </span>
              {p}
            </div>
          ))}
        </div>
      </div>

      {/* Sticky actions */}
      <div className="sticky bottom-4 mt-6 rounded-2xl border border-border bg-card/95 p-3 shadow-card backdrop-blur sm:bottom-6">
        <div className="flex flex-wrap items-center justify-center gap-2">
          <Button onClick={onRestart} className="h-11 rounded-xl px-5 font-semibold">
            <RotateCcw className="mr-1.5 h-4 w-4" />
            다시 면접 보기
          </Button>
          <Button variant="outline" className="h-11 rounded-xl px-5 font-semibold">
            <Save className="mr-1.5 h-4 w-4" />
            리포트 저장하기
          </Button>
          <Button variant="ghost" onClick={onNew} className="h-11 rounded-xl px-5 font-semibold">
            <Plus className="mr-1.5 h-4 w-4" />
            새 지원서로 시작하기
          </Button>
        </div>
      </div>
    </div>
  );
}
