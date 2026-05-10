export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-bg-base flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-accent-cyan/10 border border-accent-cyan/30 flex items-center justify-center">
              <div className="w-5 h-5 rounded border-2 border-accent-cyan" />
            </div>
            <span className="text-xl font-semibold tracking-tight text-text-primary">
              Docker Image Auditor
            </span>
          </div>
          <p className="text-text-secondary text-sm">
            AI-powered container security intelligence
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}
