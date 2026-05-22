import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { LandingScreen } from "@/components/interview/LandingScreen";
import { InputScreen } from "@/components/interview/InputScreen";
import { InterviewScreen } from "@/components/interview/InterviewScreen";
import { AnalyzingScreen } from "@/components/interview/AnalyzingScreen";
import { ReportScreen } from "@/components/interview/ReportScreen";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Interview Mate AI · 한국어 AI 모의면접" },
      { name: "description", content: "AI 면접관 4인과 함께하는 음성 기반 모의면접. 답변을 분석해 상세 피드백 리포트를 제공합니다." },
      { property: "og:title", content: "Interview Mate AI" },
      { property: "og:description", content: "실제 면접처럼 연습하고, 답변의 강점과 약점을 분석받으세요." },
    ],
  }),
  component: Index,
});

type Stage = "landing" | "input" | "interview" | "analyzing" | "report";

function Index() {
  const [stage, setStage] = useState<Stage>("landing");
  const [meta, setMeta] = useState({ company: "토스", role: "프로덕트 디자이너", sessionId: "" });

  return (
    <div className="min-h-screen bg-background">
      {stage === "landing" && <LandingScreen onStart={() => setStage("input")} />}
      {stage === "input" && (
        <InputScreen
          onBack={() => setStage("landing")}
          onStart={(d) => {
            setMeta(d);
            setStage("interview");
          }}
        />
      )}
      {stage === "interview" && (
        <InterviewScreen
          company={meta.company}
          role={meta.role}
          sessionId={meta.sessionId}
          onEnd={() => setStage("analyzing")}
        />
      )}
      {stage === "analyzing" && <AnalyzingScreen onDone={() => setStage("report")} />}
      {stage === "report" && (
        <ReportScreen
          company={meta.company}
          role={meta.role}
          sessionId={meta.sessionId}
          onRestart={() => setStage("interview")}
          onNew={() => setStage("input")}
        />
      )}
    </div>
  );
}
