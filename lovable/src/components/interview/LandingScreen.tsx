import { ArrowRight, FileText, MessageCircleQuestion, LineChart, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { interviewers } from "@/lib/interview-mock";

interface Props {
  onStart: () => void;
}

const features = [
  { icon: FileText, title: "지원서 기반 질문", desc: "자소서·이력서·포트폴리오를 분석해 맞춤형 질문을 생성합니다." },
  { icon: MessageCircleQuestion, title: "실시간 꼬리질문", desc: "답변의 맥락을 파악해 깊이 있는 후속 질문을 던집니다." },
  { icon: LineChart, title: "면접 후 피드백 리포트", desc: "답변 구조와 직무 적합성을 정량·정성 지표로 분석합니다." },
];

export function LandingScreen({ onStart }: Props) {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Sparkles className="h-4 w-4" />
          </div>
          <span className="text-[17px] font-semibold tracking-tight">Interview Mate AI</span>
        </div>
        <span className="text-sm text-muted-foreground">한국어 AI 모의면접</span>
      </header>

      <section className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-12 lg:grid-cols-2 lg:py-20">
        <div className="fade-in">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-sm text-muted-foreground shadow-soft">
            <span className="h-1.5 w-1.5 rounded-full bg-primary pulse-dot" />
            4명의 AI 면접관이 함께합니다
          </div>
          <h1 className="mt-5 text-4xl font-bold leading-[1.55] tracking-normal text-foreground sm:text-4xl">
            실제 면접처럼 연습하고,
            <br />
            답변의 강점과 약점을 분석받으세요.
          </h1>
          <p className="mt-5 max-w-xl text-[17px] leading-[1.4] text-muted-foreground">
            지원 회사와 직무, 채용공고 그리고 본인의 서류를 입력하면
            맞춤형 음성 모의면접을 진행하고, 종료 후 상세 피드백 리포트를 받아볼 수 있어요.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button size="lg" onClick={onStart} className="h-12 rounded-2xl px-6 text-[15px] font-semibold">
              모의면접 시작하기
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
            <span className="text-sm text-muted-foreground">평균 소요 시간 약 15분</span>
          </div>
        </div>

        <div className="relative">
          <div className="absolute -inset-6 -z-10 rounded-[2rem] bg-gradient-to-br from-accent/60 to-transparent blur-2xl" />
          <div className="grid grid-cols-2 gap-4">
            {interviewers.map((p, i) => (
              <div
                key={p.id}
                className="rounded-3xl border border-border bg-surface p-5 shadow-card transition-transform hover:-translate-y-0.5"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="flex items-center gap-3">
                  <img
                    src={p.avatar}
                    alt={p.name}
                    className="h-11 w-11 rounded-2xl object-cover shadow-sm"
                    loading="lazy"
                    width={44}
                    height={44}
                  />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-foreground">{p.name}</p>
                    <p className="truncate text-xs text-muted-foreground">{p.role}</p>
                  </div>
                </div>
                <p className="mt-4 line-clamp-2 text-sm leading-[1.4] text-muted-foreground">{p.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-24">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {features.map((f) => (
            <div key={f.title} className="rounded-2xl border border-border bg-surface p-6 shadow-soft">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-accent-foreground">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 text-[17px] font-semibold text-foreground">{f.title}</h3>
              <p className="mt-2 text-[15px] leading-[1.4] text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
