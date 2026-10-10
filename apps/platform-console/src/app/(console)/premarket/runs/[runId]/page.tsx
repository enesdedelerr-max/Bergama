import { PremarketRunDetailPage } from "@/components/premarket/premarket-run-detail-page";

type PremarketRunPageProps = {
  params: Promise<{ runId: string }>;
};

export default async function PremarketRunPage({
  params,
}: PremarketRunPageProps) {
  const { runId } = await params;
  return <PremarketRunDetailPage runId={decodeURIComponent(runId)} />;
}
