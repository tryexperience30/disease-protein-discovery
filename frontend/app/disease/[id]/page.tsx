import type { Metadata } from "next";
import { DiseaseExplorer } from "@/components/DiseaseExplorer";
import { apiGet } from "@/lib/api";
import type { DiseaseDetail } from "@/types";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  try {
    const d = await apiGet<DiseaseDetail>(`/api/diseases/${id}`);
    return {
      title: `${d.name} — Disease–Protein Network Explorer`,
      description: `Explore the PPI pathway and computationally predicted candidate proteins for ${d.name}.`,
    };
  } catch {
    return { title: "Disease not found" };
  }
}

export default async function DiseasePage({ params }: Props) {
  const { id } = await params;
  return <DiseaseExplorer diseaseId={id} />;
}
