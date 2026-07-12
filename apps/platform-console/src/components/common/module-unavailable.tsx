import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ModuleUnavailable({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <p className="text-[11px] font-medium tracking-[0.14em] text-[color:var(--muted-fg)] uppercase">
          Operations
        </p>
        <h1 className="font-[family-name:var(--font-display)] text-3xl tracking-tight">
          {title}
        </h1>
      </div>
      <Card data-testid="module-unavailable">
        <CardHeader>
          <CardTitle>Module not enabled</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-[color:var(--muted-fg)]">{description}</p>
        </CardContent>
      </Card>
    </div>
  );
}
