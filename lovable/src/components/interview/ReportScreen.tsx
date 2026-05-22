import { Check, AlertCircle, Lightbulb, RotateCcw, Save, Plus, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface Props {
  company: string;
  role: string;
  onRestart: () => void;
  onNew: () => void;
}

const scores = [
  { label: "직무 적합성", value: 82 },
  { label: "답변 구조화", value: 74 },
  { label: "커뮤니케이션 명확성", value: 80 },
  { label: "꼬리질문 대응력", value: 68 },
  { label: "산업/회사 이해도", value: 76 },
];

const strengths = [
  "프로젝트 경험을 구체적으로 설명했습니다.",
  "문제 해결 과정의 흐름이 명확했습니다.",
  "지원 직무에 대한 관심이 잘 드러났습니다.",
];

const improvements = [
  "성과를 수치로 표현하면 설득력이 높아집니다.",
  "답변 말미에 직무 역량과 연결하는 문장이 필요합니다.",
  "꼬리질문에서 핵심을 먼저 말하는 연습이 필요합니다.",
];

const questionFeedback = [
  {
    q: "포트폴리오에 적어주신 프로젝트 중 가장 인상 깊었던 의사결정 경험을 말씀해 주세요.",
    type: "서류 기반",
    summary: "온보딩 플로우 단순화 의사결정과 그 결과를 설명함.",
    good: "데이터 기반 의사결정 과정을 명확히 전달했습니다.",
    bad: "본인의 역할이 다소 모호하게 표현되었습니다.",
    tip: "‘제가 ~를 결정했다’와 같이 주체를 분명히 하세요.",
  },
  {
    q: "방금 말씀하신 경험에서 본인의 구체적인 기여는 무엇이었나요?",
    type: "꼬리질문",
    summary: "팀 협업 위주로 답변하여 개인 기여가 명확하지 않음.",
    good: "협업 태도가 잘 드러났습니다.",
    bad: "개인 결과물과 책임 범위가 부족했습니다.",
    tip: "STAR 구조 중 Action을 본인 중심으로 구체화하세요.",
  },
  {
    q: "이 직무에서 가장 중요한 역량은 무엇이라고 생각하시나요?",
    type: "직무 적합성",
    summary: "‘사용자 공감’을 핵심으로 답변함.",
    good: "직무 본질과 잘 연결되는 답변이었습니다.",
    bad: "본인의 사례와의 연결이 약했습니다.",
    tip: "역량 정의 → 본인 경험 → 직무 적용 순으로 구성해 보세요.",
  },
];

const practices = [
  "STAR 구조로 답변 재작성하기",
  "성과 수치화 연습",
  "지원 회사 최근 뉴스 3개 정리",
  "1분 자기소개 압축 연습",
];

export function ReportScreen({ company, role, onRestart, onNew }: Props) {
  const total = 78;
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
      {/* Hero summary — clearer hierarchy */}
      <div className="overflow-hidden rounded-3xl border border-border bg-card shadow-card fade-in">
        <div className="border-b border-border bg-gradient-to-br from-accent/40 to-transparent px-6 py-8 sm:px-10 sm:py-10">
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <span className="rounded-full bg-surface px-2.5 py-1 shadow-soft">면접 피드백 리포트</span>
            <span>2026.05.22 · 14분 32초 · 6문항</span>
          </div>

          <div className="mt-5 grid grid-cols-1 items-end gap-8 sm:grid-cols-[1fr_auto]">
            <div>
              <h1 className="text-[28px] font-bold leading-tight tracking-tight text-foreground sm:text-[36px]">
                {company} · {role}
              </h1>
              <p className="mt-3 max-w-xl text-[16px] leading-[1.4] text-muted-foreground sm:text-[17px]">
                경험 설명은 구체적이지만,{" "}
                <span className="font-medium text-foreground">직무와의 연결성</span>을 더 명확히
                보여주면 좋습니다.
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
                  상위 32%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Score breakdown inline */}
        <div className="grid grid-cols-1 gap-x-8 gap-y-4 px-6 py-6 sm:grid-cols-2 sm:px-10 sm:py-7">
          {scores.map((s) => (
            <div key={s.label}>
              <div className="flex items-center justify-between">
                <span className="text-[15px] text-foreground">{s.label}</span>
                <span className="text-sm font-semibold tabular-nums text-foreground">{s.value}</span>
              </div>
              <Progress value={s.value} className="mt-2 h-1.5 rounded-full" />
            </div>
          ))}
        </div>
      </div>

      {/* Strengths & improvements — at-a-glance */}
      <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
        <div className="rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-7">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-success/15 text-success">
              <Check className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-success">Strength</p>
              <h3 className="text-[17px] font-semibold text-foreground">잘한 점</h3>
            </div>
          </div>
          <ul className="mt-5 space-y-3.5">
            {strengths.map((t) => (
              <li key={t} className="flex gap-2.5 text-[15px] leading-[1.4] text-foreground">
                <Check className="mt-1 h-4 w-4 shrink-0 text-success" />
                {t}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-7">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-warning/20 text-warning-foreground">
              <AlertCircle className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-warning-foreground">Improve</p>
              <h3 className="text-[17px] font-semibold text-foreground">개선 포인트</h3>
            </div>
          </div>
          <ul className="mt-5 space-y-3.5">
            {improvements.map((t) => (
              <li key={t} className="flex gap-2.5 text-[15px] leading-[1.4] text-foreground">
                <AlertCircle className="mt-1 h-4 w-4 shrink-0 text-warning" />
                {t}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Per question */}
      <div className="mt-5 rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-7">
        <h2 className="text-xl font-semibold tracking-tight text-foreground">질문별 피드백</h2>
        <p className="mt-1 text-sm text-muted-foreground">각 질문을 펼쳐 상세 피드백을 확인하세요.</p>
        <Accordion type="single" collapsible className="mt-4">
          {questionFeedback.map((f, i) => (
            <AccordionItem key={i} value={`q-${i}`} className="border-b border-border last:border-0">
              <AccordionTrigger className="py-4 text-left hover:no-underline">
                <div className="flex flex-1 items-center gap-3 pr-3">
                  <Badge variant="secondary" className="shrink-0 rounded-full bg-accent text-accent-foreground">
                    {f.type}
                  </Badge>
                  <span className="text-left text-[15px] font-medium leading-[1.4] text-foreground">{f.q}</span>
                </div>
              </AccordionTrigger>
              <AccordionContent className="pb-5">
                <div className="space-y-4 rounded-2xl bg-surface-muted p-5">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">내 답변 요약</p>
                    <p className="mt-1.5 text-[15px] leading-[1.4] text-foreground">{f.summary}</p>
                  </div>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="rounded-xl bg-success/5 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wider text-success">잘한 점</p>
                      <p className="mt-1.5 text-[15px] leading-[1.4] text-foreground">{f.good}</p>
                    </div>
                    <div className="rounded-xl bg-warning/10 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wider text-warning-foreground">개선할 점</p>
                      <p className="mt-1.5 text-[15px] leading-[1.4] text-foreground">{f.bad}</p>
                    </div>
                  </div>
                  <div className="rounded-xl bg-primary/5 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wider text-primary">추천 답변 방향</p>
                    <p className="mt-1.5 text-[15px] leading-[1.4] text-foreground">{f.tip}</p>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>

      {/* Practice */}
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
