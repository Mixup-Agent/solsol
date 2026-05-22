import { Newspaper, MessageSquareQuote, FileSearch, Target, type LucideIcon } from "lucide-react";
import newsAvatar from "@/assets/interviewers/news.png";
import followupAvatar from "@/assets/interviewers/followup.png";
import documentAvatar from "@/assets/interviewers/document.png";
import fitAvatar from "@/assets/interviewers/fit.png";

export type InterviewerType = "news" | "followup" | "document" | "fit";

export interface Interviewer {
  id: InterviewerType;
  name: string;
  role: string;
  description: string;
  initial: string;
  accent: string;
  icon: LucideIcon;
  avatar: string;
}

export const interviewers: Interviewer[] = [
  {
    id: "news",
    name: "뉴스 분석 면접관",
    role: "산업·회사 동향",
    description: "최근 뉴스와 시장 변화 기반 질문",
    initial: "N",
    accent: "oklch(0.66 0.14 235)",
    icon: Newspaper,
    avatar: newsAvatar,
  },
  {
    id: "followup",
    name: "꼬리질문 면접관",
    role: "답변 심층 탐구",
    description: "답변을 깊게 파고드는 후속 질문",
    initial: "F",
    accent: "oklch(0.6 0.08 220)",
    icon: MessageSquareQuote,
    avatar: followupAvatar,
  },
  {
    id: "document",
    name: "서류 분석 면접관",
    role: "자소서·이력서·포트폴리오",
    description: "지원 서류 기반 맞춤 질문",
    initial: "D",
    accent: "oklch(0.55 0.06 250)",
    icon: FileSearch,
    avatar: documentAvatar,
  },
  {
    id: "fit",
    name: "직무 적합성 면접관",
    role: "역량·태도·컬처핏",
    description: "직무 적합성과 컬처핏 검증",
    initial: "P",
    accent: "oklch(0.62 0.05 240)",
    icon: Target,
    avatar: fitAvatar,
  },
];

export interface MockQuestion {
  interviewer: InterviewerType;
  type: string;
  text: string;
}

export const mockQuestions: MockQuestion[] = [
  { interviewer: "document", type: "서류 기반", text: "포트폴리오에 적어주신 프로젝트 중 가장 인상 깊었던 의사결정 경험을 말씀해 주세요." },
  { interviewer: "followup", type: "꼬리질문", text: "방금 말씀하신 경험에서 본인의 구체적인 기여는 무엇이었나요?" },
  { interviewer: "news", type: "뉴스 기반", text: "최근 해당 산업의 변화가 지원 직무에 어떤 영향을 줄 것이라고 보시나요?" },
  { interviewer: "fit", type: "직무 적합성", text: "이 직무에서 가장 중요하다고 생각하는 역량 한 가지와 그 이유를 말씀해 주세요." },
  { interviewer: "document", type: "서류 기반", text: "자기소개서에서 강조하신 협업 경험을 좀 더 구체적으로 설명해 주실 수 있을까요?" },
  { interviewer: "followup", type: "꼬리질문", text: "그 과정에서 가장 큰 갈등은 무엇이었고 어떻게 해결하셨나요?" },
  { interviewer: "fit", type: "직무 적합성", text: "우리 회사의 조직문화 중 본인과 가장 잘 맞는 부분은 어떤 점이라고 생각하시나요?" },
  { interviewer: "news", type: "뉴스 기반", text: "경쟁사의 최근 행보를 봤을 때, 우리 회사가 어떤 전략을 취해야 한다고 보시나요?" },
];

export const mockTranscripts = [
  "네, 제가 진행했던 프로젝트 중에서는 사용자 리텐션을 개선했던 경험이 가장 기억에 남습니다. 당시 핵심 지표가 정체되어 있었고, 데이터 분석을 통해 온보딩 단계의 이탈이 가장 크다는 점을 발견했습니다.",
  "구체적으로는 A/B 테스트를 두 차례 진행했고, 가설 검증 후 온보딩 플로우를 3단계에서 2단계로 단순화했습니다. 그 결과 7일 리텐션이 약 18퍼센트 개선되었습니다.",
  "협업 측면에서는 디자이너, 개발자 두 분과 매일 짧은 동기화 미팅을 진행했고, 의사결정 속도를 높이기 위해 의견 충돌이 생길 때마다 데이터를 기준으로 판단했습니다.",
];

export const systemMessages = [
  "면접 흐름 분석 중",
  "다음 질문 준비 중",
  "난이도 조정됨",
  "답변 품질 평가 중",
];
