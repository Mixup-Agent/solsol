import { useRef, useState } from "react";
import { Check, FileUp, Upload, ChevronRight, ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createSession } from "@/lib/api";

interface Props {
  onBack: () => void;
  onStart: (data: { company: string; role: string; sessionId: string }) => void;
}

const steps = [
  { id: 1, title: "기본 정보", desc: "회사·직무" },
  { id: 2, title: "서류 업로드", desc: "자소서·이력서·포트폴리오" },
  { id: 3, title: "채용공고", desc: "공고 링크" },
];

function FileUpload({
  label,
  required,
  file,
  onChange,
}: {
  label: string;
  required?: boolean;
  file: File | null;
  onChange: (f: File | null) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <button
      type="button"
      onClick={() => inputRef.current?.click()}
      className="group flex w-full items-center justify-between rounded-2xl border border-dashed border-border bg-surface-muted px-5 py-4 text-left transition hover:border-primary/50 hover:bg-accent/40"
    >
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${file ? "bg-success/15 text-success" : "bg-surface text-muted-foreground"}`}>
          {file ? <Check className="h-5 w-5" /> : <FileUp className="h-5 w-5" />}
        </div>
        <div>
          <p className="text-[15px] font-medium text-foreground">
            {label}
            {required && <span className="ml-1 text-destructive">*</span>}
          </p>
          <p className="text-sm text-muted-foreground">
            {file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)}MB` : "PDF 파일을 클릭하여 업로드"}
          </p>
        </div>
      </div>
      <Upload className="h-4 w-4 text-muted-foreground" />
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
      />
    </button>
  );
}

export function InputScreen({ onBack, onStart }: Props) {
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [link, setLink] = useState("");
  const [selfIntroFile, setSelfIntroFile] = useState<File | null>(null);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [portfolioFile, setPortfolioFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = company && role && link && selfIntroFile && resumeFile && portfolioFile;

  const handleStart = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("self_intro_file", selfIntroFile!);
    formData.append("resume_file", resumeFile!);
    formData.append("portfolio_file", portfolioFile!);
    formData.append("company", company);
    formData.append("role", role);
    formData.append("job_posting_url", link);

    try {
      const session = await createSession(formData);
      onStart({ company, role, sessionId: String(session.session_id) });
    } catch (e) {
      setError("세션 생성에 실패했습니다. 서버 연결을 확인해 주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          홈으로
        </button>
        <span className="text-sm font-medium text-foreground">면접 준비</span>
      </header>

      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-8 px-6 pb-16 lg:grid-cols-[260px_1fr]">
        <aside>
          <div className="rounded-2xl border border-border bg-surface p-5 shadow-soft lg:sticky lg:top-6">
            <p className="text-sm font-medium text-muted-foreground">진행 단계</p>
            <ol className="mt-4 space-y-1">
              {steps.map((s, i) => (
                <li
                  key={s.id}
                  className={`flex items-start gap-3 rounded-xl px-3 py-3 ${i === 0 ? "bg-accent/60" : ""}`}
                >
                  <div className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${i === 0 ? "bg-primary text-primary-foreground" : "bg-surface-muted text-muted-foreground"}`}>
                    {s.id}
                  </div>
                  <div>
                    <p className="text-[15px] font-medium text-foreground">{s.title}</p>
                    <p className="text-sm text-muted-foreground">{s.desc}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </aside>

        <main className="space-y-6">
          <section className="rounded-3xl border border-border bg-card p-7 shadow-card">
            <h2 className="text-xl font-semibold text-foreground">지원 정보</h2>
            <p className="mt-1 text-sm text-muted-foreground">지원 정보를 바탕으로 맞춤형 면접 질문을 생성합니다.</p>
            <div className="mt-6 grid grid-cols-1 gap-5 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="company">회사명 <span className="text-destructive">*</span></Label>
                <Input id="company" placeholder="예: 토스" value={company} onChange={(e) => setCompany(e.target.value)} className="h-11 rounded-xl" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role">지원 직무 <span className="text-destructive">*</span></Label>
                <Input id="role" placeholder="예: 프로덕트 디자이너" value={role} onChange={(e) => setRole(e.target.value)} className="h-11 rounded-xl" />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="link">채용공고 링크 <span className="text-destructive">*</span></Label>
                <Input id="link" placeholder="https://" value={link} onChange={(e) => setLink(e.target.value)} className="h-11 rounded-xl" />
              </div>
            </div>
          </section>

          <section className="rounded-3xl border border-border bg-card p-7 shadow-card">
            <h2 className="text-xl font-semibold text-foreground">서류 업로드</h2>
            <p className="mt-1 text-sm text-muted-foreground">자소서, 이력서, 포트폴리오를 업로드하면 더 정교한 질문이 생성됩니다.</p>
            <div className="mt-6 space-y-3">
              <FileUpload label="자기소개서 PDF" required file={selfIntroFile} onChange={setSelfIntroFile} />
              <FileUpload label="이력서 PDF" required file={resumeFile} onChange={setResumeFile} />
              <FileUpload label="포트폴리오 PDF" required file={portfolioFile} onChange={setPortfolioFile} />
            </div>
          </section>

          {error && (
            <p className="rounded-2xl border border-destructive/30 bg-destructive/5 px-5 py-3 text-sm text-destructive">
              {error}
            </p>
          )}

          <div className="flex items-center justify-between rounded-2xl border border-border bg-surface px-5 py-4 shadow-soft">
            <p className="text-sm text-muted-foreground">입력하신 정보는 면접 종료 후 삭제됩니다.</p>
            <Button
              size="lg"
              onClick={handleStart}
              disabled={!canSubmit || loading}
              className="h-12 rounded-2xl px-6 text-[15px] font-semibold"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  분석 중...
                </>
              ) : (
                <>
                  면접 시작
                  <ChevronRight className="ml-0.5 h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </main>
      </div>
    </div>
  );
}
